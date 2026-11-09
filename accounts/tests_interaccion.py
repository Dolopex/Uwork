"""Tests de la interaccion de los formularios.

Los formularios largos de U-Work (registro de estudiante, registro de
empleador, publicacion de un trabajo) se resuelven con un asistente por
pasos. Estos tests blindan tres cosas:

1. Que el asistente esta montado: un paso visible, navegacion y el modulo
   compartido que lo controla.
2. Que los controles con estado (medidor de contrasena, contador,
   etiquetas) declaran sus atributos en el HTML. Si el atributo viaja en
   el servidor, el formulario no depende del orden de carga de los
   scripts.
3. Que no se vuelve al patron de scroll que el asistente sustituyo: un
   listener de scroll recalcula en cada cuadro de la pagina.
"""
import re
from pathlib import Path

from django.test import TestCase
from django.urls import reverse

from .forms import EmployerRegisterForm, StudentRegisterForm

RAIZ = Path(__file__).resolve().parent.parent
MODULO = RAIZ / 'static' / 'js' / 'wizard.js'

PLANTILLAS_ASISTENTE = (
    'templates/accounts/register_student.html',
    'templates/accounts/register_employer.html',
    'templates/jobs/job_form.html',
)


class AsistentePorPasosTests(TestCase):
    """El formulario largo se resuelve paso a paso, no bajando y llenando."""

    def test_las_plantillas_montan_el_asistente(self):
        for relativa in PLANTILLAS_ASISTENTE:
            with self.subTest(plantilla=relativa):
                texto = (RAIZ / relativa).read_text(encoding='utf-8')
                self.assertIn('data-wizard', texto)
                self.assertIn('data-step-panel', texto)
                self.assertIn('data-step-target', texto)
                self.assertIn('data-step-next', texto)
                self.assertIn('data-step-back', texto)

    def test_las_plantillas_cargan_el_modulo_compartido(self):
        """Un solo archivo de JavaScript para los tres formularios."""
        for relativa in PLANTILLAS_ASISTENTE:
            with self.subTest(plantilla=relativa):
                texto = (RAIZ / relativa).read_text(encoding='utf-8')
                self.assertIn("js/wizard.js", texto)

    def test_solo_el_paso_uno_arranca_visible(self):
        """Los demas pasos nacen ocultos: no se llenan campos a ciegas."""
        respuesta = self.client.get(reverse('accounts:register_student'))
        html = respuesta.content.decode('utf-8')
        activos = re.findall(r'class="step-panel is-active" data-step-panel="(\d+)"', html)
        self.assertEqual(activos, ['1'])

    def test_el_indicador_de_paso_se_anuncia(self):
        """El avance se comunica a los lectores de pantalla."""
        respuesta = self.client.get(reverse('accounts:register_student'))
        html = respuesta.content.decode('utf-8')
        self.assertIn('data-step-meta', html)
        self.assertIn('aria-live="polite"', html)

    def test_el_boton_de_avance_tiene_texto_de_espera(self):
        """El estado de envio se ve: el boton dice que esta trabajando."""
        respuesta = self.client.get(reverse('accounts:register_student'))
        html = respuesta.content.decode('utf-8')
        self.assertIn('data-submit-label', html)
        self.assertIn('data-submit-pending', html)

    def test_el_error_del_servidor_abre_el_paso_correspondiente(self):
        """Un error del servidor no deja a la persona en un paso vacio.

        El campo invalido lleva aria-invalid, asi que el modulo puede
        abrir el paso que lo contiene.
        """
        respuesta = self.client.post(reverse('accounts:register_student'), {
            'username': '',
            'email': 'no-es-institucional@gmail.com',
        })
        html = respuesta.content.decode('utf-8')
        self.assertIn('aria-invalid="true"', html)
        self.assertIn('data-error-link', html)

    def test_el_resumen_de_errores_enlaza_a_los_campos(self):
        """WCAG 3.3.1: el resumen apunta al campo con el problema."""
        respuesta = self.client.post(reverse('accounts:register_student'), {
            'username': '', 'email': 'no-es-institucional@gmail.com',
        })
        html = respuesta.content.decode('utf-8')
        self.assertIn('href="#id_username"', html)
        self.assertIn('href="#id_email"', html)

    def test_la_plantilla_declara_el_enlace_al_campo(self):
        """El enlace se construye con el id del campo, no fijo."""
        texto = (RAIZ / 'templates' / 'accounts' / 'register_student.html') \
            .read_text(encoding='utf-8')
        self.assertIn('href="#{{ field.id_for_label }}"', texto)


class ControlesConEstadoTests(TestCase):
    """Los controles con estado declaran sus atributos en el servidor."""

    def test_el_modulo_compartido_existe(self):
        self.assertTrue(MODULO.exists())
        self.assertIn('iniciarAsistente', MODULO.read_text(encoding='utf-8'))

    def test_el_medidor_comes_del_servidor(self):
        """El atributo viaja en el HTML: no depende del orden de scripts."""
        form = StudentRegisterForm()
        self.assertEqual(
            form.fields['password1'].widget.attrs.get('data-password-meter'), 'true')
        self.assertEqual(
            form.fields['password2'].widget.attrs.get('data-password-match'),
            'id_password1')

    def test_la_ayuda_de_contrasena_esta_en_espanol(self):
        """UserCreationForm traia el texto de ayuda en ingles."""
        form = StudentRegisterForm()
        self.assertIn('Mínimo 8 caracteres', form.fields['password1'].help_text)
        self.assertIn('Contraseña', form.fields['password1'].label)
        self.assertIn('Confirmar contraseña', form.fields['password2'].label)

    def test_las_habilidades_declaran_el_control_de_etiquetas(self):
        form = StudentRegisterForm()
        self.assertEqual(
            form.fields['habilidades'].widget.attrs.get('data-tags'), 'true')

    def test_el_empleador_tiene_los_mismos_controles(self):
        form = EmployerRegisterForm()
        self.assertEqual(
            form.fields['password1'].widget.attrs.get('data-password-meter'), 'true')
        self.assertEqual(
            form.fields['password2'].widget.attrs.get('data-password-match'),
            'id_password1')


class SinListenersDeScrollTests(TestCase):
    """El scroll no se escucha: se recalcula en cada cuadro de la pagina.

    El asistente sustituyo el progreso por scroll de los formularios
    antiguos. El patron no debe volver.
    """

    PLANTILLAS = PLANTILLAS_ASISTENTE + (
        'templates/accounts/login.html',
        'templates/accounts/role_select.html',
        'templates/jobs/apply.html',
        'templates/support/ticket_form.html',
    )

    def test_ninguna_plantilla_escucha_el_scroll(self):
        for relativa in self.PLANTILLAS:
            with self.subTest(plantilla=relativa):
                texto = (RAIZ / relativa).read_text(encoding='utf-8')
                limpio = re.sub(r'<!--.*?-->', '', texto, flags=re.S)
                limpio = re.sub(r'//.*', '', limpio)
                self.assertNotIn("addEventListener('scroll'", limpio)
                self.assertNotIn('addEventListener("scroll"', limpio)

    def test_el_modulo_compartido_tampoco_escucha_el_scroll(self):
        texto = MODULO.read_text(encoding='utf-8')
        self.assertNotIn("addEventListener('scroll'", texto)
        self.assertNotIn('addEventListener("scroll"', texto)
