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
