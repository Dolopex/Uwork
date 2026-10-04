"""Tests de los requisitos R10 y R11 de software_pendientes.txt.

R10 — Whitelist de correos institucionales
R11 — Verificación de email con link de confirmación
"""
from datetime import timedelta

from django.contrib.auth import authenticate
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import EmployerRegisterForm, StudentRegisterForm
from .models import User


class R10WhitelistInstitucionalTests(TestCase):
    """R10 — el estudiante solo puede registrarse con dominio institucional."""

    def _datos(self, **over):
        base = dict(
            username='testuser', first_name='Test', last_name='User',
            email='test@campusuninunez.edu.co',
            password1='Aa12345678xyz!', password2='Aa12345678xyz!',
        )
        base.update(over)
        return base

    def test_dominio_institucional_es_aceptado(self):
        form = StudentRegisterForm(self._datos())
        self.assertTrue(form.is_valid(), form.errors)

    def test_dominio_personal_es_rechazado(self):
        form = StudentRegisterForm(self._datos(email='test@gmail.com'))
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_subdominio_falso_es_rechazado(self):
        """'@dominio.edu.co.evil.com' no debe pasar por institutional."""
        form = StudentRegisterForm(
            self._datos(email='test@campusuninunez.edu.co.evil.com'))
        self.assertFalse(form.is_valid())

    def test_comparacion_de_dominio_es_case_insensitive(self):
        form = StudentRegisterForm(self._datos(email='test@CAMPUSUNINUNEZ.EDU.CO'))
        self.assertTrue(form.is_valid(), form.errors)

    def test_empleador_puede_usar_correo_personal(self):
        """§5: los empleadores se registran con email personal."""
        form = EmployerRegisterForm(self._datos(email='empleador@suempresa.com'))
        self.assertTrue(form.is_valid(), form.errors)


class R11VerificacionEmailTests(TestCase):
    """R11 — la cuenta solo se activa tras confirmar el correo."""

    def setUp(self):
        # La caché no se revierte entre tests, así que el rate-limit de
        # /register/ (compartido por IP) contaminaría otros tests.
        from django.core.cache import cache
        cache.clear()

        self.url_registro = reverse('accounts:register_employer')
        self.datos = dict(
            username='nuevo', first_name='Nuevo', last_name='User',
            email='nuevo@empresa.com',
            password1='Aa12345678xyz!', password2='Aa12345678xyz!',
        )

    def _registrar(self):
        return self.client.post(self.url_registro, self.datos)

    def test_registro_no_inicia_sesion(self):
        self._registrar()
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_registro_redirige_a_revision_de_correo(self):
        respuesta = self._registrar()
        self.assertRedirects(
            respuesta, reverse('accounts:check_email'), target_status_code=200)

    def test_cuenta_nace_sin_verificar_con_token(self):
        self._registrar()
        usuario = User.objects.get(username='nuevo')
        self.assertFalse(usuario.is_email_verified)
        self.assertIsNotNone(usuario.email_verification_token)

    def test_login_es_rechazado_antes_de_verificar(self):
        self._registrar()
        self.assertIsNone(
            authenticate(username='nuevo', password='Aa12345678xyz!'))

    def test_login_avisa_que_falta_verificar(self):
        self._registrar()
        respuesta = self.client.post(
            reverse('accounts:login'),
            {'username': 'nuevo', 'password': 'Aa12345678xyz!'},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'no está verificado')
        self.assertContains(respuesta, 'Reenviar verificación')

    def test_verificar_con_token_valido_activa_la_cuenta(self):
        self._registrar()
        usuario = User.objects.get(username='nuevo')

        self.client.get(reverse('accounts:verify_email',
                                args=[usuario.email_verification_token]))

        usuario.refresh_from_db()
        self.assertTrue(usuario.is_email_verified)
        self.assertIsNone(usuario.email_verification_sent_at)

    def test_login_funciona_tras_verificar(self):
        self._registrar()
        usuario = User.objects.get(username='nuevo')
        self.client.get(reverse('accounts:verify_email',
                                args=[usuario.email_verification_token]))

        self.assertIsNotNone(
            authenticate(username='nuevo', password='Aa12345678xyz!'))

    def test_token_inexistente_muestra_error(self):
        import uuid
        respuesta = self.client.get(
            reverse('accounts:verify_email', args=[uuid.uuid4()]))
        self.assertContains(respuesta, 'Enlace no válido')

    def test_token_vencido_no_activa_la_cuenta(self):
        self._registrar()
        usuario = User.objects.get(username='nuevo')
        token = usuario.email_verification_token
        User.objects.filter(pk=usuario.pk).update(
            email_verification_sent_at=timezone.now() - timedelta(hours=49))

        respuesta = self.client.get(reverse('accounts:verify_email', args=[token]))

        usuario.refresh_from_db()
        self.assertFalse(usuario.is_email_verified)
        self.assertContains(respuesta, 'venció')

    def test_reutilizar_token_es_idempotente(self):
        self._registrar()
        usuario = User.objects.get(username='nuevo')
        url = reverse('accounts:verify_email',
                      args=[usuario.email_verification_token])

        self.client.get(url)
        respuesta = self.client.get(url)

        self.assertContains(respuesta, 'Ya estaba verificado')

    def test_reenvio_no_revela_si_el_correo_existe(self):
        """Anti-enumeración: misma respuesta exista o no la cuenta."""
        User.objects.create_user(username='pendiente',
                                 email='pendiente@empresa.com',
                                 password='Aa12345678xyz!')
        url = reverse('accounts:resend_verification')

        inexistente = self.client.post(
            url, {'email': 'nadie@noexiste.com'}, follow=True)
        existente = self.client.post(
            url, {'email': 'pendiente@empresa.com'}, follow=True)

        self.assertEqual(len(inexistente.content), len(existente.content))
        self.assertContains(inexistente, 'Si ese correo tiene una cuenta')

    def test_una_sesion_forzada_no_evita_el_bloqueo(self):
        """El gate no solo actúa en authenticate(): también al leer la sesión.

        ModelBackend.get_user() consulta user_can_authenticate(), así que
        una cuenta sin verificar no recupera sesión aunque exista la cookie.
        """
        usuario = User.objects.create_user(username='sinsesion',
                                           email='sinsesion@empresa.com',
                                           password='Aa12345678xyz!')
        self.client.force_login(usuario)

        # accounts:profile es @login_required; jobs:job_list es público y
        # no serviría para comprobar el gate.
        respuesta = self.client.get(reverse('accounts:profile'))

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse('accounts:login'), respuesta.url)


class R16EliminarCuentaTests(TestCase):
    """R16 — derecho de supresión (Ley 1581 de 2012, art. 17)."""

    PASSWORD = 'Aa12345678xyz!'

    def setUp(self):
        from jobs.models import Application, Job
        from notifications.models import Notification
        from reviews.models import Review
        from support.models import SupportTicket

        # R11 exige is_email_verified para que la sesión exista, también
        # cuando se fuerza el login: get_user() consulta user_can_authenticate.
        self.estudiante = User.objects.create_user(
            username='est', email='est@campusuninunez.edu.co',
            password=self.PASSWORD, rol=User.Rol.ESTUDIANTE,
            is_email_verified=True)
        self.empleador = User.objects.create_user(
            username='emp', email='emp@empresa.com',
            password=self.PASSWORD, rol=User.Rol.EMPLEADOR,
            is_email_verified=True)

        self.trabajo = Job.objects.create(
            titulo='Prueba', descripcion='x', creador=self.empleador,
            fecha_limite='2030-01-01', pago=1000)
        self.postulacion = Application.objects.create(
            usuario=self.estudiante, trabajo=self.trabajo)
        self.review = Review.objects.create(
            autor=self.empleador, receptor=self.estudiante,
            trabajo=self.trabajo, puntuacion=5)
        self.notificacion = Notification.objects.create(
            usuario=self.empleador, mensaje='notificacion del que borra')
        self.notificacion_ajena = Notification.objects.create(
            usuario=self.estudiante, mensaje='notificacion de otro usuario')
        self.ticket = SupportTicket.objects.create(
            reporter=self.empleador, tipo='bug', descripcion='x del que borra')

        self.Job = Job
        self.Application = Application
        self.Review = Review
        self.Notification = Notification
        self.SupportTicket = SupportTicket

        self.url = reverse('accounts:delete_account')

    def test_la_vista_exige_iniciar_sesion(self):
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse('accounts:login'), respuesta.url)

    def test_muestra_el_resumen_de_datos_a_borrar(self):
        self.client.force_login(self.empleador)
        respuesta = self.client.get(self.url)
        self.assertContains(respuesta, 'Se eliminará lo siguiente')
        self.assertContains(respuesta, 'Trabajos que publicaste')
        self.assertContains(respuesta, 'Ley 1581 de 2012')

    def test_no_borra_si_la_contrasena_no_coincide(self):
        self.client.force_login(self.empleador)
        respuesta = self.client.post(self.url, {'password': 'incorrecta'})

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(User.objects.filter(pk=self.empleador.pk).exists())
        self.assertContains(respuesta, 'La contraseña no coincide')

    def test_elimina_la_cuenta_tras_confirmar(self):
        self.client.force_login(self.empleador)
        respuesta = self.client.post(self.url, {'password': self.PASSWORD},
                                     follow=True)

        self.assertFalse(User.objects.filter(pk=self.empleador.pk).exists())
        self.assertRedirects(
            respuesta, reverse('accounts:role_select'),
            target_status_code=200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_elimina_en_cascada_los_registros_relacionados(self):
        self.client.force_login(self.empleador)
        self.client.post(self.url, {'password': self.PASSWORD})

        self.assertFalse(self.Job.objects.filter(pk=self.trabajo.pk).exists())
        self.assertFalse(
            self.Application.objects.filter(pk=self.postulacion.pk).exists())
        self.assertFalse(
            self.Review.objects.filter(pk=self.review.pk).exists())
        self.assertFalse(
            self.Notification.objects.filter(
                pk=self.notificacion.pk).exists())
        self.assertFalse(
            self.SupportTicket.objects.filter(pk=self.ticket.pk).exists())

    def test_conserva_los_datos_de_otros_usuarios(self):
        """La cascada no debe tocar lo que pertenece a terceros."""
        ticket_ajeno = self.SupportTicket.objects.create(
            reporter=self.estudiante, tipo='bug', descripcion='de otro usuario')

        self.client.force_login(self.empleador)
        self.client.post(self.url, {'password': self.PASSWORD})

        self.assertTrue(User.objects.filter(pk=self.estudiante.pk).exists())
        self.assertTrue(
            self.Notification.objects.filter(
                pk=self.notificacion_ajena.pk).exists())
        self.assertTrue(
            self.SupportTicket.objects.filter(pk=ticket_ajeno.pk).exists())


class R16BorradoDeArchivosTests(TestCase):
    """El borrado de la cuenta también elimina los archivos de MEDIA_ROOT."""

    def setUp(self):
        import tempfile
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import override_settings

        self.media = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.media)
        self.override.enable()
        self.addCleanup(self.override.disable)

        self.contrasena = 'Aa12345678xyz!'
        self.usuario = User.objects.create_user(
            username='confoto', email='confoto@empresa.com',
            password=self.contrasena)
        self.usuario.foto.save(
            'perfil.png', SimpleUploadedFile('perfil.png', b'falso-png'),
            save=True)

    def test_elimina_el_archivo_de_foto_del_disco(self):
        import os

        from .deletion import eliminar_archivos_de_usuario

        ruta = self.usuario.foto.path
        self.assertTrue(os.path.isfile(ruta))

        eliminados = eliminar_archivos_de_usuario(self.usuario)

        self.assertEqual(eliminados, 1)
        self.assertFalse(os.path.isfile(ruta))

    def test_no_puede_borrar_fuera_de_media_root(self):
        """Un nombre con '..' no debe sacar el borrado de MEDIA_ROOT."""
        from .deletion import _ruta_absoluta

        self.assertIsNone(_ruta_absoluta('../../secreto.txt'))
