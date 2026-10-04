"""Tests de las páginas legales públicas — R14 y R15.

R14 — Términos y Condiciones (Indicador: Página pública)
R15 — Política de Privacidad (Indicador: Página pública)

El documento de pendientes exige que sean "visibles para todos los usuarios
antes del primer uso", así que deben responder sin iniciar sesión.
"""
from django.test import TestCase
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

    def test_marca_los_bloques_pendientes_de_redaccion_legal(self):
        respuesta = self.client.get(reverse('legal:terminos'))
        self.assertContains(respuesta, 'Documento en revisión')
        self.assertContains(respuesta, 'class="pendiente"')

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

    def test_marca_los_bloques_pendientes_de_redaccion_legal(self):
        respuesta = self.client.get(reverse('legal:privacidad'))
        self.assertContains(respuesta, 'Documento en revisión')
        self.assertContains(respuesta, 'class="pendiente"')


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
