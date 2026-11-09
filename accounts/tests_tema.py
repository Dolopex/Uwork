"""Tests del tema claro / oscuro.

El tema estaba repartido en cuatro sitios: el <script> que lo aplicaba en
base.html, otra copia en login.html, otra en la seleccion de rol y ninguna
en la pantalla de verificacion de correo. Las pantallas independientes no
heredan de base.html, asi que se quedaban con el fondo blanco del
navegador en tema oscuro y sin interruptor para cambiarlo.

Estos tests comprueban que hay un solo lugar que decide y que todas las
pantallas lo usan.
"""
from pathlib import Path

from django.test import TestCase
from django.urls import reverse

RAIZ = Path(__file__).resolve().parent.parent

#: Pantallas que se ven sin iniciar sesion. El resto heredan de base.html
#: y el tema llega por ahi.
PANTALLAS_PUBLICAS = (
    'accounts:role_select',
    'accounts:login',
    'accounts:register_student',
    'accounts:register_employer',
    'accounts:check_email',
    'accounts:password_reset',
)


class UnSoloLugarParaElTemaTests(TestCase):
    """El tema se decide en un solo sitio."""

    def test_el_modulo_del_tema_existe(self):
        self.assertTrue((RAIZ / 'static' / 'js' / 'theme.js').exists())

    def test_el_fragmento_de_cabeza_es_un_include(self):
        """La lectura de localStorage vive en un fragmento compartido."""
        parcial = RAIZ / 'templates' / 'partials' / 'theme_head.html'
        self.assertTrue(parcial.exists())
        self.assertIn('uwork-theme', parcial.read_text(encoding='utf-8'))

    def test_ninguna_plantilla_define_el_tema_por_su_cuenta(self):
        """Solo el fragmento compartido lee localStorage.

        Con cuatro copias del mismo script, cambiar el tema en una
        pantalla podia dejar a las otras con el icono sin actualizar.
        """
        copias = []
        for plantilla in (RAIZ / 'templates').rglob('*.html'):
            texto = plantilla.read_text(encoding='utf-8')
            if 'localStorage.getItem(' in texto and 'partials' not in str(plantilla):
                copias.append(plantilla.relative_to(RAIZ).as_posix())
        self.assertEqual(copias, [], 'Hay copias del script de tema')

    def test_ninguna_plantilla_tiene_el_script_de_tema_propio(self):
        for nombre in ('templates/base.html',
                       'templates/accounts/login.html',
                       'templates/accounts/role_select.html'):
            texto = (RAIZ / nombre).read_text(encoding='utf-8')
            self.assertNotIn('function alternarTema', texto)
            self.assertNotIn('function toggleTheme', texto)

    def test_base_html_carga_el_modulo_compartido(self):
        texto = (RAIZ / 'templates' / 'base.html').read_text(encoding='utf-8')
        self.assertIn('js/theme.js', texto)

    def test_el_interruptor_es_un_include(self):
        parcial = RAIZ / 'templates' / 'partials' / 'theme_toggle.html'
        self.assertTrue(parcial.exists())
        self.assertIn('data-theme-toggle', parcial.read_text(encoding='utf-8'))


class ElFondoVieneDeLaHojaDeSistemaTests(TestCase):
    """El fondo del cuerpo vive en style.css, no en base.html.

    Con la regla en base.html, las pantallas independientes se quedaban
    con el fondo blanco del navegador: el tema oscuro se Switching a dark
    solo se veia en las tarjetas, no en la pagina.
    """

    def setUp(self):
        self.sistema = (RAIZ / 'static' / 'css' / 'style.css').read_text(
            encoding='utf-8')
        self.base = (RAIZ / 'templates' / 'base.html').read_text(encoding='utf-8')

    def test_la_hoja_de_sistema_pinta_el_cuerpo(self):
        self.assertIn('body {', self.sistema)
        self.assertIn('background: var(--bg);', self.sistema)

    def test_base_html_no_redefine_el_fondo_del_cuerpo(self):
        self.assertNotIn('background: var(--bg);', self.base)

    def test_los_controles_de_formulario_tambien_estan_en_la_hoja(self):
        """Mismo motivo: login no hereda de base.html."""
        self.assertIn('.form-control, .form-select {', self.sistema)
        self.assertIn('background: var(--input-bg);', self.sistema)

    def test_el_foco_visible_esta_en_la_hoja(self):
        self.assertIn(':focus-visible {', self.sistema)


class CadaPantallaTieneInterruptorTests(TestCase):
    """En toda pantalla se puede cambiar de tema."""

    def test_las_pantallas_publicas_responden(self):
        for nombre in PANTALLAS_PUBLICAS:
            with self.subTest(pantalla=nombre):
                respuesta = self.client.get(reverse(nombre))
                self.assertEqual(respuesta.status_code, 200)

    def test_el_tema_se_aplica_al_llegar(self):
        """La pagina trae el script que aplica el tema antes de pintar.

        El tema vive en localStorage, que es del navegador: el servidor no
        puede saberlo. Lo que se comprueba es que la pagina trae el
        fragmento que lo aplica, para que no haya destello al recargar.
        """
        for nombre in PANTALLAS_PUBLICAS:
            with self.subTest(pantalla=nombre):
                respuesta = self.client.get(reverse(nombre))
                self.assertIn(b"localStorage.getItem('uwork-theme')",
                              respuesta.content)
                self.assertIn(b"setAttribute('data-theme','dark')",
                              respuesta.content)

    def test_las_pantallas_publicas_tienen_el_interruptor(self):
        for nombre in PANTALLAS_PUBLICAS:
            with self.subTest(pantalla=nombre):
                respuesta = self.client.get(reverse(nombre))
                self.assertContains(respuesta, 'data-theme-toggle')


class LasPantallasNoHeredanDeBaseTests(TestCase):
    """Registro de las pantallas independientes.

    Si una de estas vuelve a heredar de base.html, el interruptor fijo
    se duplicaria. El test lo avisa.
    """

    INDEPENDIENTES = (
        'templates/accounts/login.html',
        'templates/accounts/role_select.html',
        'templates/accounts/_verify_base.html',
    )

    def test_no_extienden_base(self):
        for relativa in self.INDEPENDIENTES:
            with self.subTest(plantilla=relativa):
                texto = (RAIZ / relativa).read_text(encoding='utf-8')
                self.assertNotIn("extends 'base.html'", texto)

    def test_las_que_lo_necesitan_cargan_el_modulo_del_tema(self):
        for relativa in self.INDEPENDIENTES:
            with self.subTest(plantilla=relativa):
                texto = (RAIZ / relativa).read_text(encoding='utf-8')
                self.assertIn('js/theme.js', texto)

    def test_la_base_de_contrasenas_hereda_del_modulo(self):
        """_password_base.html extiende _verify_base.html: hereda el tema."""
        texto = (RAIZ / 'templates' / 'accounts' / '_password_base.html') \
            .read_text(encoding='utf-8')
        self.assertIn("extends 'accounts/_verify_base.html'", texto)
        self.assertNotIn('js/theme.js', texto)

    def test_ninguna_pantalla_usa_una_paleta_propia(self):
        """Los tokens(--v-*) eran una paleta paralela a la de la casa."""
        for relativa in self.INDEPENDIENTES:
            with self.subTest(plantilla=relativa):
                texto = (RAIZ / relativa).read_text(encoding='utf-8')
                self.assertNotIn('--v-bg:', texto)
                self.assertNotIn('--v-card:', texto)
                self.assertNotIn('--v-text:', texto)
