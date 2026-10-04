"""Tests de los controles de seguridad y la moderación.

§6.5.3 — Controles de seguridad pendientes
§6.5.4 — Moderación de contenido
"""
import io
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.upload_validators import validar_imagen
from jobs.models import Job
from moderation.models import Apelacion, Reporte, Sancion

User = get_user_model()

# PNG minimo valido: firma magica + IHDR.
PNG = (b'\x89PNG\r\n\x1a\n' + b'\x00\x00\x00\rIHDR' + b'\x00' * 40)
JPEG = b'\xff\xd8\xff\xe0' + b'\x00' * 40


def png(nombre='foto.png', tipo='image/png', bytes_extra=0):
    return SimpleUploadedFile(nombre, PNG + b'\x00' * bytes_extra,
                              content_type=tipo)


class ValidacionUploadTests(TestCase):
    """§6.5.3 — 'Validación MIME y de tamaño real en uploads'."""

    def test_acepta_un_png_real(self):
        validar_imagen(png())  # no debe lanzar

    def test_acepta_un_jpeg_real(self):
        validar_imagen(SimpleUploadedFile('f.jpg', JPEG,
                                         content_type='image/jpeg'))

    @override_settings(UPLOAD_MAX_SIZE_MB=1)
    def test_rechaza_archivo_que_supera_el_tamano(self):
        grande = png(bytes_extra=2 * 1024 * 1024)
        with self.assertRaises(ValidationError):
            validar_imagen(grande)

    def test_rechaza_archivo_vacio(self):
        with self.assertRaises(ValidationError):
            validar_imagen(SimpleUploadedFile('vacia.png', b'',
                                             content_type='image/png'))

    def test_rechaza_script_con_extension_de_imagen(self):
        """Un .php renombrado a .png no debe pasar la validación."""
        peligroso = SimpleUploadedFile('shell.png', b'<?php system($_GET[0]); ?>',
                                       content_type='image/png')
        with self.assertRaises(ValidationError) as ctx:
            validar_imagen(peligroso)
        self.assertIn('mime', str(ctx.exception.code))

    def test_rechaza_mime_declarado_que_no_corresponde(self):
        """Declara JPEG pero el contenido es PNG: no debe pasar."""
        mentiroso = SimpleUploadedFile('f.png', PNG, content_type='image/jpeg')
        with self.assertRaises(ValidationError):
            validar_imagen(mentiroso)

    def test_rechaza_extension_no_permitida(self):
        archivo = SimpleUploadedFile('doc.pdf', PDF := b'%PDF-1.4' + b'\x00' * 40,
                                     content_type='application/pdf')
        with self.assertRaises(ValidationError):
            validar_imagen(archivo)

    def test_webp_valido_se_acepta(self):
        webp = b'RIFF' + b'\x00\x00\x00\x00' + b'WEBP' + b'\x00' * 20
        validar_imagen(SimpleUploadedFile('f.webp', webp,
                                         content_type='image/webp'))


class RateLimitTests(TestCase):
    """§6.5.3 — 'Rate-limiting en endpoints sensibles'."""

    def setUp(self):
        # La caché es global al proceso y no se revierte entre tests: sin
        # limpiarla, los contadores de otra clase afectarían a estos.
        cache.clear()
        self.addCleanup(cache.clear)

    def test_limita_intentos_de_login(self):
        from django.conf import settings

        limite = settings.RATE_LIMITS['/login/']['limit']
        for _ in range(limite):
            respuesta = self.client.post(
                reverse('accounts:login'),
                {'username': 'noexiste', 'password': 'malaclave'})
            self.assertEqual(respuesta.status_code, 200)

        # El intento siguiente ya excede el límite.
        respuesta = self.client.post(
            reverse('accounts:login'),
            {'username': 'noexiste', 'password': 'malaclave'})
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse('accounts:login'), respuesta.url)

    def test_limita_el_registro(self):
        from django.conf import settings

        limite = settings.RATE_LIMITS['/register/']['limit']
        for _ in range(limite):
            self.client.post(reverse('accounts:register_employer'), {})

        respuesta = self.client.post(reverse('accounts:register_employer'), {})
        self.assertEqual(respuesta.status_code, 429)
        self.assertIn('Retry-After', respuesta)

    def test_no_limita_las_peticiones_de_lectura(self):
        for _ in range(30):
            respuesta = self.client.get(reverse('jobs:job_list'))
            self.assertEqual(respuesta.status_code, 200)


class BaneoYForceLogoutTests(TestCase):
    """§6.5.3 — 'Mecanismo de force-logout para usuarios baneados'."""

    def setUp(self):
        self.usuario = User.objects.create_user(
            username='baneado', email='b@x.com', password='Aa12345678xyz!',
            is_email_verified=True)
        self.url = reverse('accounts:profile')

    def test_un_usuario_sancionado_cierra_sesion(self):
        self.client.force_login(self.usuario)
        self.usuario.aplicar_baneo('Contenido prohibido')

        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse('accounts:login'), respuesta.url)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_el_baneo_temporal_expira_solo(self):
        self.client.force_login(self.usuario)
        self.usuario.aplicar_baneo('Temporal',
                                   hasta=timezone.now() - timedelta(hours=1))

        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, 200)
        self.usuario.refresh_from_db()
        self.assertFalse(self.usuario.is_banned)

    def test_baneo_permanente_no_expira(self):
        self.usuario.aplicar_baneo('Permanente')
        self.assertTrue(self.usuario.baneo_vigente)
        self.assertIsNone(self.usuario.baneo_hasta)

    def test_levantar_el_baneo_devuelve_el_acceso(self):
        self.usuario.aplicar_baneo('Error')
        self.usuario.levantar_baneo()
        self.client.force_login(self.usuario)

        self.assertEqual(self.client.get(self.url).status_code, 200)


class ReportesTests(TestCase):
    """§6.5.4 — 'Sistema de reportes por usuarios'."""

    def setUp(self):
        self.empleador = User.objects.create_user(
            username='emp1', email='e1@x.com', password='Aa12345678xyz!',
            rol=User.Rol.EMPLEADOR, is_email_verified=True)
        self.estudiante = User.objects.create_user(
            username='est1', email='s1@campusuninunez.edu.co',
            password='Aa12345678xyz!', rol=User.Rol.ESTUDIANTE,
            is_email_verified=True)
        self.staff = User.objects.create_user(
            username='mod', email='mod@x.com', password='Aa12345678xyz!',
            is_staff=True, is_email_verified=True)
        self.trabajo = Job.objects.create(
            titulo='Oferta sospechosa', descripcion='x', creador=self.empleador,
            fecha_limite='2030-01-01', pago=1000)

    def test_un_usuario_puede_reportar(self):
        self.client.force_login(self.estudiante)

        respuesta = self.client.post(
            reverse('moderation:reportar_trabajo', args=[self.trabajo.pk]),
            {'motivo': 'estafa', 'descripcion': 'Piden dinero adelantado'})

        self.assertEqual(respuesta.status_code, 302)
        reporte = Reporte.objects.get()
        self.assertEqual(reporte.motivo, 'estafa')
        self.assertEqual(reporte.reportante, self.estudiante)

    def test_no_se_puede_reportar_la_propia_publicacion(self):
        self.client.force_login(self.empleador)

        self.client.post(
            reverse('moderation:reportar_trabajo', args=[self.trabajo.pk]),
            {'motivo': 'otro'})

        self.assertEqual(Reporte.objects.count(), 0)

    def test_no_hay_reportes_duplicados_abiertos(self):
        self.client.force_login(self.estudiante)
        url = reverse('moderation:reportar_trabajo', args=[self.trabajo.pk])

        self.client.post(url, {'motivo': 'estafa'})
        self.client.post(url, {'motivo': 'violencia'})

        self.assertEqual(Reporte.objects.count(), 1)

    def test_el_reporte_asigna_plazo_de_sla(self):
        from django.conf import settings

        self.client.force_login(self.estudiante)
        self.client.post(
            reverse('moderation:reportar_trabajo', args=[self.trabajo.pk]),
            {'motivo': 'estafa'})

        reporte = Reporte.objects.get()
        self.assertIsNotNone(reporte.plazo_respuesta)
        self.assertFalse(reporte.sla_vencido)
        self.assertLess(
            reporte.plazo_respuesta,
            timezone.now() + timedelta(hours=settings.MODERATION_SLA_HOURS + 1))

    def test_sla_vencido_se_detecta(self):
        self.client.force_login(self.estudiante)
        self.client.post(
            reverse('moderation:reportar_trabajo', args=[self.trabajo.pk]),
            {'motivo': 'estafa'})
        reporte = Reporte.objects.get()
        Reporte.objects.filter(pk=reporte.pk).update(
            plazo_respuesta=timezone.now() - timedelta(hours=1))

        reporte.refresh_from_db()
        self.assertTrue(reporte.sla_vencido)

    def test_el_panel_exige_ser_staff(self):
        self.client.force_login(self.estudiante)
        respuesta = self.client.get(reverse('moderation:panel_reportes'))
        self.assertNotEqual(respuesta.status_code, 200)

        self.client.force_login(self.staff)
        respuesta = self.client.get(reverse('moderation:panel_reportes'))
        self.assertEqual(respuesta.status_code, 200)

    def test_el_panel_muestra_primero_los_vencidos(self):
        vencido = Reporte.objects.create(
            trabajo=self.trabajo, reportante=self.estudiante,
            motivo='estafa', plazo_respuesta=timezone.now() - timedelta(hours=2))
        en_curso = Reporte.objects.create(
            trabajo=Job.objects.create(titulo='Otro', descripcion='x',
                                      creador=self.empleador,
                                      fecha_limite='2030-01-01', pago=1),
            reportante=self.estudiante, motivo='otro',
            plazo_respuesta=timezone.now() + timedelta(hours=10))

        self.client.force_login(self.staff)
        respuesta = self.client.get(reverse('moderation:panel_reportes'))

        self.assertContains(respuesta, 'SLA vencido')
        self.assertEqual(list(respuesta.context['reportes_vencidos']), [vencido])
        self.assertEqual(list(respuesta.context['reportes_en_curso']), [en_curso])


class SancionesTests(TestCase):
    """§6.5.4 — bitácora de auditoría, baneo temporal y permanente."""

    def setUp(self):
        self.moderador = User.objects.create_user(
            username='mod', email='mod@x.com', password='Aa12345678xyz!',
            is_staff=True, is_email_verified=True)
        self.empleador = User.objects.create_user(
            username='mal', email='mal@x.com', password='Aa12345678xyz!',
            rol=User.Rol.EMPLEADOR, is_email_verified=True)
        self.trabajo = Job.objects.create(
            titulo='Oferta', descripcion='x', creador=self.empleador,
            fecha_limite='2030-01-01', pago=1000)
        self.reporte = Reporte.objects.create(
            trabajo=self.trabajo, reportante=self.moderador,
            motivo='ilegal', plazo_respuesta=timezone.now() + timedelta(hours=48))

    def test_sancionar_crea_la_bitacora_y_bansea(self):
        self.client.force_login(self.moderador)

        self.client.post(
            reverse('moderation:resolver_reporte', args=[self.reporte.pk]),
            {'accion': 'sancionar', 'tipo_sancion': 'permanente',
             'motivo_sancion': 'Oferta de contenido ilegal'})

        sancion = Sancion.objects.get()
        self.assertEqual(sancion.tipo, Sancion.Tipo.PERMANENTE)
        self.assertEqual(sancion.aplicada_por, self.moderador)
        self.assertEqual(sancion.usuario, self.empleador)
        self.empleador.refresh_from_db()
        self.assertTrue(self.empleador.is_banned)
        self.reporte.refresh_from_db()
        self.assertEqual(self.reporte.estado, Reporte.Estado.RESUELTO)

    def test_baneo_temporal_registra_la_fecha_de_vencimiento(self):
        self.client.force_login(self.moderador)

        self.client.post(
            reverse('moderation:resolver_reporte', args=[self.reporte.pk]),
            {'accion': 'sancionar', 'tipo_sancion': 'temporal', 'dias': '30',
             'motivo_sancion': 'Repeticion'})

        sancion = Sancion.objects.get()
        self.assertEqual(sancion.tipo, Sancion.Tipo.TEMPORAL)
        self.assertIsNotNone(sancion.hasta)
        self.empleador.refresh_from_db()
        # Baneo activo: aún no vence.
        self.assertTrue(self.empleador.baneo_vigente)

    def test_la_bitacora_registra_quien_que_cuando_y_por_que(self):
        self.client.force_login(self.moderador)
        self.client.post(
            reverse('moderation:resolver_reporte', args=[self.reporte.pk]),
            {'accion': 'sancionar', 'tipo_sancion': 'permanente',
             'motivo_sancion': 'Estafa'})

        sancion = Sancion.objects.get()
        for campo in ('aplicada_por', 'usuario', 'created_at', 'motivo'):
            self.assertIsNotNone(getattr(sancion, campo), campo)

    def test_retirar_contenido_cierra_el_reporte(self):
        self.client.force_login(self.moderador)

        self.client.post(
            reverse('moderation:resolver_reporte', args=[self.reporte.pk]),
            {'accion': 'retirar'})

        self.assertFalse(Job.objects.filter(pk=self.trabajo.pk).exists())
        self.reporte.refresh_from_db()
        self.assertEqual(self.reporte.resolucion, Reporte.Resolucion.RETIRADO)

    def test_levantar_sancion_conserva_el_registro_original(self):
        self.client.force_login(self.moderador)
        self.client.post(
            reverse('moderation:resolver_reporte', args=[self.reporte.pk]),
            {'accion': 'sancionar', 'tipo_sancion': 'permanente',
             'motivo_sancion': 'Error de moderacion'})

        sancion = Sancion.objects.get()
        self.client.post(
            reverse('moderation:levantar_sancion', args=[sancion.pk]))

        sancion.refresh_from_db()
        self.assertFalse(sancion.vigente)
        self.assertIsNotNone(sancion.levantada_por)
        self.assertIsNotNone(sancion.levantada_at)
        self.assertEqual(sancion.motivo, 'Error de moderacion')
        self.empleador.refresh_from_db()
        self.assertFalse(self.empleador.is_banned)


class ApelaciónTests(TestCase):
    """§6.5.4 — 'Canal de apelación para usuarios sancionados'."""

    def setUp(self):
        self.moderador = User.objects.create_user(
            username='mod', email='mod@x.com', password='Aa12345678xyz!',
            is_staff=True, is_email_verified=True)
        self.usuario = User.objects.create_user(
            username='sanc', email='sanc@x.com', password='Aa12345678xyz!',
            is_email_verified=True)
        self.sancion = Sancion.objects.create(
            usuario=self.usuario, aplicada_por=self.moderador,
            tipo=Sancion.Tipo.TEMPORAL, motivo='Supuesto contenido ilegal',
            hasta=timezone.now() + timedelta(days=7))
        self.usuario.aplicar_baneo('Supuesto contenido ilegal',
                                   hasta=self.sancion.hasta)

    def test_registrar_apelacion(self):
        apelacion = Apelacion.objects.create(
            sancion=self.sancion, usuario=self.usuario,
            motivo='No era mi publicacion')

        self.assertTrue(apelacion.pendiente)

    def test_aceptar_apelacion_levanta_el_baneo(self):
        apelacion = Apelacion.objects.create(
            sancion=self.sancion, usuario=self.usuario, motivo='Error')
        self.client.force_login(self.moderador)

        self.client.post(
            reverse('moderation:resolver_apelacion', args=[apelacion.pk]),
            {'decision': 'aceptar', 'respuesta': 'Revisado, se levanta'})

        apelacion.refresh_from_db()
        self.assertEqual(apelacion.estado, Apelacion.Estado.ACEPTADA)
        self.usuario.refresh_from_db()
        self.assertFalse(self.usuario.is_banned)
        self.sancion.refresh_from_db()
        self.assertFalse(self.sancion.vigente)

    def test_rechazar_apelacion_mantiene_el_baneo(self):
        apelacion = Apelacion.objects.create(
            sancion=self.sancion, usuario=self.usuario, motivo='No')
        self.client.force_login(self.moderador)

        self.client.post(
            reverse('moderation:resolver_apelacion', args=[apelacion.pk]),
            {'decision': 'rechazar', 'respuesta': 'La sanción se mantiene'})

        apelacion.refresh_from_db()
        self.assertEqual(apelacion.estado, Apelacion.Estado.RECHAZADA)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.is_banned)

    def test_no_se_resuelve_sin_respuesta(self):
        apelacion = Apelacion.objects.create(
            sancion=self.sancion, usuario=self.usuario, motivo='X')
        self.client.force_login(self.moderador)

        self.client.post(
            reverse('moderation:resolver_apelacion', args=[apelacion.pk]),
            {'decision': 'aceptar', 'respuesta': ''})

        apelacion.refresh_from_db()
        self.assertTrue(apelacion.pendiente)


class PasswordResetTests(TestCase):
    """§6.5.3 — vistas de 'Olvidé mi contraseña' y cambio de contraseña.

    También cierra la vista que R2 declara faltante en el módulo de
    autenticación (Indicador: 3/4 vistas).
    """

    def setUp(self):
        self.usuario = User.objects.create_user(
            username='reset', email='reset@x.com', password='Aa12345678xyz!',
            is_email_verified=True)

    def test_la_vista_de_olvide_mi_contrasena_es_publica(self):
        respuesta = self.client.get(reverse('accounts:password_reset'))
        self.assertEqual(respuesta.status_code, 200)

    def test_el_login_enlaza_a_la_recuperacion(self):
        respuesta = self.client.get(reverse('accounts:login'))
        self.assertContains(respuesta, reverse('accounts:password_reset'))

    def test_solicitar_el_enlace_no_revela_si_el_correo_existe(self):
        respuesta = self.client.post(
            reverse('accounts:password_reset'),
            {'email': 'nadie@noexiste.com'}, follow=True)

        self.assertContains(respuesta, 'Revisa tu correo')

    def test_el_token_valido_cambia_la_contrasena(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        uid = urlsafe_base64_encode(force_bytes(self.usuario.pk))
        token = default_token_generator.make_token(self.usuario)
        url = reverse('accounts:password_reset_confirm',
                      args=[uid, token])

        # Django 5.2 mueve el token a la sesión y redirige a una URL sin
        # token, para que no viaje en el Referer.
        respuesta = self.client.get(url, follow=True)
        self.assertContains(respuesta, 'Crea tu contraseña nueva')

        url_set_password = respuesta.redirect_chain[-1][0]
        respuesta = self.client.post(url_set_password, {
            'new_password1': 'NuevaClave123!',
            'new_password2': 'NuevaClave123!',
        })
        self.assertEqual(respuesta.status_code, 302)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('NuevaClave123!'))

    def test_un_token_invalido_no_permite_cambiar_la_contrasena(self):
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        uid = urlsafe_base64_encode(force_bytes(self.usuario.pk))
        url = reverse('accounts:password_reset_confirm',
                      args=[uid, 'token-falso'])

        respuesta = self.client.get(url, follow=True)

        self.assertContains(respuesta, 'Enlace no válido')
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('Aa12345678xyz!'))

    def test_cambiar_contrasena_exige_sesion(self):
        respuesta = self.client.get(reverse('accounts:password_change'))
        self.assertEqual(respuesta.status_code, 302)

    def test_cambiar_contrasena_autenticado(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.get(reverse('accounts:password_change'))
        self.assertEqual(respuesta.status_code, 200)

        respuesta = self.client.post(reverse('accounts:password_change'), {
            'old_password': 'Aa12345678xyz!',
            'new_password1': 'OtraClave456!',
            'new_password2': 'OtraClave456!',
        })
        self.assertEqual(respuesta.status_code, 302)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('OtraClave456!'))

    def test_el_perfil_enlaza_al_cambio_de_contrasena(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.get(reverse('accounts:profile'))
        self.assertContains(respuesta, reverse('accounts:password_change'))


class SecurityHeadersTests(TestCase):
    """§6.5.3 — headers de seguridad."""

    def test_headers_de_serie(self):
        respuesta = self.client.get(reverse('jobs:job_list'))

        self.assertEqual(respuesta.headers.get('X-Content-Type-Options'),
                         'nosniff')
        self.assertEqual(respuesta.headers.get('Referrer-Policy'),
                         'strict-origin-when-cross-origin')
        self.assertEqual(respuesta.headers.get('X-Frame-Options'), 'DENY')

    def test_hsts_solo_en_produccion(self):
        with override_settings(SECURE_HSTS_SECONDS=31536000,
                               SECURE_SSL_REDIRECT=True):
            respuesta = self.client.get(reverse('jobs:job_list'),
                                        secure=True)
            self.assertIn('Strict-Transport-Security', respuesta.headers)

    def test_csp_declara_sitios_externos_permitidos(self):
        with override_settings(CSP_DEFAULT_SRC=["'self'"],
                               CSP_SCRIPT_SRC=["'self'",
                                               'https://cdn.jsdelivr.net']):
            from accounts.middleware import RateLimitMiddleware
            # La configuración existe y no permite scripts inline arbitrarios.
            from django.conf import settings
            self.assertNotIn("'unsafe-inline'", settings.CSP_SCRIPT_SRC)
            self.assertEqual(settings.CSP_FRAME_ANCESTORS, ["'none'"])
