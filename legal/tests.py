"""Tests de las páginas legales públicas — R14 y R15.

R14 — Términos y Condiciones (Indicador: Página pública)
R15 — Política de Privacidad (Indicador: Página pública)

El documento de pendientes exige que sean "visibles para todos los usuarios
antes del primer uso", así que deben responder sin iniciar sesión.
"""
from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse


class R14TerminosYCondicionesTests(TestCase):
    """R14 — Términos y Condiciones publicados."""

    def test_la_pagina_es_publica(self):
        respuesta = self.client.get(reverse('legal:terminos'))
        self.assertEqual(respuesta.status_code, 200)

    def test_contiene_las_secciones_declaradas(self):
        respuesta = self.client.get(reverse('legal:terminos'))
        for fragmento in ('Aceptación de los términos',
                          'Contenido prohibido',
                          'Moderación del contenido',
                          'Derechos del usuario',
                          'Legislación aplicable'):
            self.assertContains(respuesta, fragmento)

    def test_incluye_las_categorias_de_contenido_prohibido(self):
        """Las siete categorías declaradas en §6.5.4 del documento."""
        respuesta = self.client.get(reverse('legal:terminos'))
        for categoria in ('discriminación', 'suplantación de identidad',
                          'estafa o fraude', 'trabajo infantil',
                          'Incite a la violencia'):
            self.assertContains(respuesta, categoria)

    def test_declara_el_dominio_institucional_de_r10(self):
        respuesta = self.client.get(reverse('legal:terminos'))
        self.assertContains(respuesta, 'campusuninunez.edu.co')

    @override_settings(LEGAL_MOSTRAR_ANEXO=True)
    def test_marca_los_bloques_pendientes_de_redaccion_legal(self):
        """Con el anexo activo, los pendientes quedan señalados."""
        respuesta = self.client.get(reverse('legal:terminos'))
        self.assertContains(respuesta, 'Documento en revisión')
        self.assertContains(respuesta, 'class="pendiente"')

    def test_los_bloques_pendientes_no_se_publican_por_defecto(self):
        """El documento sale limpio mientras la institucion define."""
        respuesta = self.client.get(reverse('legal:terminos'))
        self.assertNotContains(respuesta, 'Documento en revisión')
        self.assertNotContains(respuesta, 'class="pendiente"')

    def test_enlaza_a_la_politica_de_privacidad(self):
        respuesta = self.client.get(reverse('legal:terminos'))
        self.assertContains(respuesta, reverse('legal:privacidad'))


class R15PoliticaDePrivacidadTests(TestCase):
    """R15 — Política de Privacidad publicada."""

    def test_la_pagina_es_publica(self):
        respuesta = self.client.get(reverse('legal:privacidad'))
        self.assertEqual(respuesta.status_code, 200)

    def test_cita_el_marco_legal(self):
        """R15 exige cumplir el principio de necesidad (art. 4 y 6)."""
        respuesta = self.client.get(reverse('legal:privacidad'))
        self.assertContains(respuesta, 'Ley 1581 de 2012')
        self.assertContains(respuesta, 'Decreto 1377 de 2013')
        self.assertContains(respuesta, 'Necesidad')

    def test_incluye_el_inventario_de_datos_declarado(self):
        """Los campos que el documento dice que sí se recolectan."""
        respuesta = self.client.get(reverse('legal:privacidad'))
        for campo in ('Nombre de usuario', 'Nombres y apellidos', 'Cédula',
                      'Teléfono', 'Fecha de nacimiento', 'Dirección',
                      'Correo electrónico institucional', 'Universidad',
                      'Carrera', 'Semestre', 'Foto de perfil',
                      'Foto de carné institucional', 'Habilidades'):
            self.assertContains(respuesta, campo)

    def test_declara_los_datos_que_no_se_recolectan(self):
        """Principio de necesidad: las categorías del §6.2."""
        respuesta = self.client.get(reverse('legal:privacidad'))
        for campo in ('Origen racial', 'Orientación política',
                      'Convicciones religiosas', 'Datos de salud',
                      'Orientación sexual'):
            self.assertContains(respuesta, campo)

    def test_documenta_el_derecho_de_supresion_de_r16(self):
        respuesta = self.client.get(reverse('legal:privacidad'))
        self.assertContains(respuesta, 'artículo 15')
        self.assertContains(respuesta, 'Suprimir sus datos')
        self.assertContains(respuesta, 'art. 17')

    def test_declara_la_residencia_de_los_datos(self):
        """Limitación (b) de §6.2: AWS US East 1."""
        respuesta = self.client.get(reverse('legal:privacidad'))
        self.assertContains(respuesta, 'AWS US East 1')
        self.assertContains(respuesta, 'Virginia')

    def test_declara_la_carencia_de_backups_propios(self):
        """Limitación (c) de §6.2."""
        respuesta = self.client.get(reverse('legal:privacidad'))
        self.assertContains(respuesta, 'copias de seguridad')
        self.assertContains(respuesta, 'punto en el tiempo')

    @override_settings(LEGAL_MOSTRAR_ANEXO=True)
    def test_marca_los_bloques_pendientes_de_redaccion_legal(self):
        """Con el anexo activo, los pendientes quedan señalados."""
        respuesta = self.client.get(reverse('legal:privacidad'))
        self.assertContains(respuesta, 'Documento en revisión')
        self.assertContains(respuesta, 'class="pendiente"')

    def test_los_bloques_pendientes_no_se_publican_por_defecto(self):
        """El documento sale limpio mientras la institucion define."""
        respuesta = self.client.get(reverse('legal:privacidad'))
        self.assertNotContains(respuesta, 'Documento en revisión')
        self.assertNotContains(respuesta, 'class="pendiente"')


class EnlacesLegalesTests(TestCase):
    """Los documentos deben ser alcanzables desde la interfaz."""

    def test_el_pie_de_pagina_enlaza_ambos_documentos(self):
        respuesta = self.client.get(reverse('jobs:job_list'))
        self.assertContains(respuesta, reverse('legal:terminos'))
        self.assertContains(respuesta, reverse('legal:privacidad'))

    def test_la_primera_pantalla_enlaza_ambos_documentos(self):
        """'visibles para todos los usuarios antes del primer uso'."""
        respuesta = self.client.get(reverse('accounts:role_select'))
        self.assertContains(respuesta, reverse('legal:terminos'))
        self.assertContains(respuesta, reverse('legal:privacidad'))


class EstructuraDelDocumentoTests(TestCase):
    """Los documentos se leen como documentos.

    Antes cada bloque pendiente era una caja punteada repetida a lo largo
    del texto: el documento parecia un borrador en quince lugares
    distintos en vez de uno solo. Ahora los pendientes viven en un anexo
    unico y el resto del texto esta escrito.
    """

    RUTAS = ('legal:terminos', 'legal:privacidad')

    def test_cada_documento_tiene_indice_con_enlaces_a_sus_secciones(self):
        for nombre in self.RUTAS:
            with self.subTest(documento=nombre):
                respuesta = self.client.get(reverse(nombre))
                html = respuesta.content.decode('utf-8')
                self.assertIn('class="doc-toc"', html)
                # Cada entrada del indice apunta a un ancla que existe.
                import re
                anclas = set(re.findall(r'href="#([a-z]+)"', html))
                for ancla in anclas:
                    self.assertIn('id="{}"'.format(ancla), html)

    def test_cada_documento_declara_su_ultima_actualizacion(self):
        for nombre in self.RUTAS:
            with self.subTest(documento=nombre):
                respuesta = self.client.get(reverse(nombre))
                self.assertContains(respuesta, 'Última actualización')
                self.assertContains(respuesta, '5 de noviembre de 2026')
                self.assertContains(respuesta, 'Versión')

    @override_settings(LEGAL_MOSTRAR_ANEXO=True)
    def test_los_pendientes_estan_concentrados_en_el_anexo(self):
        """Un solo lugar donde la institucion tiene que decidir."""
        for nombre in self.RUTAS:
            with self.subTest(documento=nombre):
                respuesta = self.client.get(reverse(nombre))
                html = respuesta.content.decode('utf-8')
                self.assertIn('Anexo. Decisiones que corresponden a la institución', html)
                # El bloque de pendientes va despues del cuerpo, no dentro.
                self.assertLess(
                    html.index('class="doc-body"'),
                    html.index('class="doc-annex"'))

    @override_settings(LEGAL_MOSTRAR_ANEXO=True)
    def test_el_anexo_enumera_los_puntos_pendientes(self):
        for nombre in self.RUTAS:
            with self.subTest(documento=nombre):
                respuesta = self.client.get(reverse(nombre))
                html = respuesta.content.decode('utf-8')
                self.assertIn('class="pendiente"', html)
                self.assertIn('Documento en revisión', html)

    @override_settings(LEGAL_MOSTRAR_ANEXO=False)
    def test_el_anexo_se_puede_ocultar(self):
        """Mientras la institucion define lo pendiente, no se publica.

        El texto principal se sigue mostrando completo: lo que se oculta
        es la lista de decisiones pendientes, no el documento.
        """
        secciones = {
            'legal:terminos': 'Aceptación de los términos',
            'legal:privacidad': 'Marco legal aplicable',
        }
        for nombre, seccion in secciones.items():
            with self.subTest(documento=nombre):
                respuesta = self.client.get(reverse(nombre))
                html = respuesta.content.decode('utf-8')
                self.assertNotIn('Anexo. Decisiones que corresponden', html)
                self.assertNotIn('class="pendiente"', html)
                self.assertNotIn('Documento en revisión', html)
                # El indice tampoco lleva una entrada que no lleva a ninguna parte.
                self.assertNotIn('href="#anexo-titulo"', html)
                # Y el documento principal sigue ahi.
                self.assertIn('class="doc-body"', html)
                self.assertIn(seccion, html)

    @override_settings(LEGAL_MOSTRAR_ANEXO=True)
    def test_el_anexo_se_puede_volver_a_mostrar(self):
        for nombre in self.RUTAS:
            with self.subTest(documento=nombre):
                respuesta = self.client.get(reverse(nombre))
                html = respuesta.content.decode('utf-8')
                self.assertIn('Anexo. Decisiones que corresponden', html)
                self.assertIn('href="#anexo-titulo"', html)

    def test_el_anexo_esta_oculto_por_defecto(self):
        """El setting viene apagado: no se publica nada sin decision."""
        self.assertFalse(settings.LEGAL_MOSTRAR_ANEXO)

    def test_el_documento_tiene_barra_de_lectura(self):
        """La barra se dibuja con la linea de tiempo de scroll: sin
        listeners de scroll."""
        for nombre in self.RUTAS:
            with self.subTest(documento=nombre):
                respuesta = self.client.get(reverse(nombre))
                self.assertContains(respuesta, 'class="doc-progress"')

    def test_el_indice_se_activa_al_leer(self):
        """El indice marca la seccion en lectura (scroll-spy)."""
        for nombre in self.RUTAS:
            with self.subTest(documento=nombre):
                respuesta = self.client.get(reverse(nombre))
                html = respuesta.content.decode('utf-8')
                self.assertIn('IntersectionObserver', html)
                self.assertIn("querySelectorAll('.doc-toc a[href^=\"#\"]')", html)
