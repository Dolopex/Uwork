"""Tests de accesibilidad del frontend — §6.6 del documento de pendientes.

El documento declara "WCAG 2.1 PARCIAL" y lista como pendientes el contraste,
la navegacion por teclado, los roles ARIA, el skip-to-content, el foco
visible y los mensajes de error accesibles. Estos tests blindan lo que ya
esta implementado para que una refactorizacion no lo rompa en silencio.
"""
import re
from pathlib import Path

from django.test import TestCase
from django.urls import reverse

RAIZ = Path(__file__).resolve().parent.parent
BASE = (RAIZ / 'templates' / 'base.html').read_text(encoding='utf-8')
# Los tokens viven en la hoja de sistema compartida; base.html solo aporta
# el maquetado. El contraste se mide sobre la fuente de verdad.
SISTEMA = (RAIZ / 'static' / 'css' / 'style.css').read_text(encoding='utf-8')


def hex_rgb(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lum(rgb):
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a, b):
    la, lb = lum(hex_rgb(a)), lum(hex_rgb(b))
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def tokens(bloque):
    """Tokens declarados, con su valor literal (hex o referencia var())."""
    return dict(re.findall(r'(--[a-z0-9-]+)\s*:\s*([^;]+);', bloque))


def resolver(tk, nombre, visto=None):
    """Sigue las referencias var() hasta llegar al color real.

    Sin esto, un token que apunta a otro (--card-bg: var(--surface)) se
    mediría como si no existiera y el test passaría sin comprobar nada.
    """
    if nombre not in tk:
        return None
    visto = visto or set()
    if nombre in visto:
        return None
    visto = visto | {nombre}
    valor = tk[nombre].strip()
    m = re.fullmatch(r'var\(\s*(--[a-z0-9-]+)\s*\)', valor)
    if m:
        return resolver(tk, m.group(1), visto)
    return valor if valor.startswith('#') else None


RAIZ_TOKENS = tokens(re.search(r':root\s*\{(.*?)\n\s*\}', SISTEMA, re.S).group(1))
# El tema oscuro hereda del claro y redefine lo que necesita.
OSCURO = dict(RAIZ_TOKENS)
OSCURO.update(
    tokens(re.search(r'\[data-theme="dark"\]\s*\{(.*?)\n\s*\}', SISTEMA, re.S).group(1)))


class ContrasteTokensTests(TestCase):
    """WCAG 1.4.3 — todo texto debe alcanzar 4.5:1."""

    def test_pares_de_texto_alcanzan_aa(self):
        pares = [
            ('--text', '--card-bg', 4.5),
            ('--text-secondary', '--card-bg', 4.5),
            ('--text-secondary', '--surface-alt', 4.5),
            ('--text-secondary', '--surface', 4.5),
            ('--text', '--bg', 4.5),
            ('--nav-text', '--card-bg', 4.5),
            ('--input-placeholder', '--input-bg', 4.5),
            ('--badge-indigo-text', '--badge-indigo-bg', 4.5),
            ('--badge-blue-text', '--badge-blue-bg', 4.5),
            ('--badge-amber-text', '--badge-amber-bg', 4.5),
            ('--badge-red-text', '--badge-red-bg', 4.5),
            ('--badge-green-text', '--badge-green-bg', 4.5),
            ('--badge-gray-text', '--badge-gray-bg', 4.5),
            ('--primary', '--card-bg', 4.5),
            ('--brand-ink', '--brand-soft', 4.5),
            ('--state-success', '--card-bg', 4.5),
            ('--state-warning', '--card-bg', 4.5),
            ('--state-danger', '--card-bg', 4.5),
            ('--state-info', '--card-bg', 4.5),
            ('--money', '--card-bg', 4.5),
        ]
        fallos = []
        for fg, bg, minimo in pares:
            for etiqueta, tk in (('claro', RAIZ_TOKENS), ('oscuro', OSCURO)):
                c_fg, c_bg = resolver(tk, fg), resolver(tk, bg)
                if c_fg is None or c_bg is None:
                    continue
                r = ratio(c_fg, c_bg)
                if r < minimo:
                    fallos.append('{} {} sobre {} = {:.2f}:1'.format(
                        etiqueta, fg, bg, r))
        self.assertEqual(fallos, [], 'Contraste insuficiente: ' + '; '.join(fallos))

    def test_bordes_de_control_alcanzan_3_1(self):
        """WCAG 1.4.11 — el borde del control debe ser distinguible."""
        for etiqueta, tk in (('claro', RAIZ_TOKENS), ('oscuro', OSCURO)):
            borde, fondo = resolver(tk, '--input-border'), resolver(tk, '--input-bg')
            self.assertIsNotNone(borde, etiqueta)
            self.assertIsNotNone(fondo, etiqueta)
            r = ratio(borde, fondo)
            self.assertGreaterEqual(
                r, 3.0,
                'Borde de input {} solo alcanza {:.2f}:1'.format(etiqueta, r))


class FocoVisibleTests(TestCase):
    """WCAG 2.4.7 - todo control interactivo muestra foco."""

    def test_define_anillo_de_foco_visible(self):
        """El anillo vive en la hoja de sistema.

        base.html solo aporta el maquetado con barra lateral. El anillo
        esta en static/css/style.css porque lo necesitan TODAS las
        pantallas, incluidas las que no heredan de base.html (login,
        seleccion de rol, verificacion de correo).
        """
        self.assertIn(':focus-visible', SISTEMA)

    def test_el_anillo_usa_outline_no_solo_box_shadow(self):
        """outline se respeta en el alto contraste de Windows."""
        bloque = re.search(r'(?m)^:focus-visible\s*\{(.*?)\}', SISTEMA, re.S)
        self.assertIsNotNone(bloque)
        self.assertIn('outline:', bloque.group(1))

    def test_no_se_elimina_el_contorno_en_controles(self):
        """outline:none sin alternativa es un anti-patron.

        Se exceptuan los destinos que no son controles: el destino del
        skip-link (el anillo sobre todo el contenido seria ruido visual)
        y el titulo del paso del asistente (recibe el foco para que el
        teclado quede ahi al cambiar de paso).
        """
        permitidos = ('#contenido-principal:focus', '.step-panel__title:focus')
        for nombre, texto in (('base.html', BASE), ('style.css', SISTEMA)):
            for coincidencia in re.finditer(
                    r'([^{}]+)\{[^{}]*outline:\s*none', texto):
                selector = coincidencia.group(1).strip().splitlines()[-1].strip()
                self.assertTrue(
                    any(selector.startswith(p) for p in permitidos),
                    'outline:none en un control de {}: {}'.format(nombre, selector))


class SkipLinkTests(TestCase):
    """WCAG 2.4.1 — mecanismo para saltar bloques de contenido."""

    def test_existe_el_enlace_de_salto(self):
        self.assertIn('class="skip-link"', BASE)
        self.assertIn('Saltar al contenido principal', BASE)

    def test_apunta_al_contenido_principal(self):
        self.assertIn('href="#contenido-principal"', BASE)

    def test_el_contenido_principal_puede_recibir_foco(self):
        """tabindex=-1 es necesario para que el salto funcione."""
        self.assertIn('id="contenido-principal"', BASE)
        self.assertRegex(BASE, r'id="contenido-principal"[^>]*tabindex="-1"')

    def test_el_enlace_esta_oculto_hasta_recibir_foco(self):
        self.assertRegex(BASE, r'\.skip-link\s*\{[^}]*top:\s*-100px')
        self.assertRegex(BASE, r'\.skip-link:focus\s*\{[^}]*top:\s*0')


class MovimientoReducidoTests(TestCase):
    """prefers-reduced-motion es un pendiente declarado en §6.6."""

    def test_respeta_prefers_reduced_motion(self):
        """La regla vive en la hoja de sistema, que cargan todas las
        pantallas: base.html solo cubre a sus propias hijas."""
        self.assertIn('prefers-reduced-motion', SISTEMA)
        self.assertRegex(SISTEMA, r'@media\s*\(prefers-reduced-motion:\s*reduce\)')

    def test_desactiva_transiciones_y_animaciones(self):
        bloque = re.search(
            r'@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{(.*?)\n\}',
            SISTEMA, re.S)
        self.assertIsNotNone(bloque)
        self.assertIn('transition-duration', bloque.group(1))
        self.assertIn('animation-duration', bloque.group(1))


class RolesAriaTests(TestCase):
    """WCAG 4.1.2 — los controles tienen nombre accesible."""

    def test_las_navegaciones_tienen_nombre(self):
        self.assertIn('aria-label="Navegación principal"', BASE)
        self.assertIn('aria-label="Menú lateral"', BASE)

    def test_los_iconos_decorativos_estan_ocultos(self):
        self.assertIn('aria-hidden="true"', BASE)

    def test_el_fondo_animado_esta_oculto_lectores(self):
        """El orbe de fondo no aporta informacion: no debe anunciarse."""
        self.assertRegex(BASE, r'app-bg-scene" aria-hidden="true"')

    def test_los_botones_de_icono_tienen_aria_label(self):
        """Un boton solo con icono necesita nombre accesible."""
        for patron in ('Cerrar sesión', 'Cambiar tema', 'Iniciar sesión',
                       'Notificaciones'):
            self.assertIn('aria-label="{}'.format(patron), BASE)

    def test_el_boton_de_cerrar_toast_tiene_nombre(self):
        self.assertIn('aria-label="Cerrar notificación"', BASE)


class ErroresDeFormularioTests(TestCase):
    """WCAG 3.3.1 y 4.1.3 — los errores se anuncian y se asocian."""

    def test_los_errores_en_linea_usan_role_alert(self):
        total = 0
        for ruta in (RAIZ / 'templates').rglob('*.html'):
            texto = ruta.read_text(encoding='utf-8')
            for coincidencia in re.finditer(
                    r'<div class="text-danger[^"]*"([^>]*)>', texto):
                total += 1
                self.assertIn(
                    'role="alert"', coincidencia.group(1),
                    '{}: un error sin role="alert" no se anuncia'.format(
                        ruta.name))
        self.assertGreater(total, 0, 'No se encontraron errores en linea')

    def test_los_formularios_de_registro_tienen_resumen_de_errores(self):
        """Resumen enfocable: role=alert + tabindex=-1."""
        for nombre in ('register_student.html', 'register_employer.html'):
            texto = (RAIZ / 'templates' / 'accounts' / nombre).read_text(
                encoding='utf-8')
            self.assertIn('id="error-summary"', texto, nombre)
            bloque = re.search(r'<div[^>]*id="error-summary"[^>]*>', texto)
            self.assertIsNotNone(bloque, nombre)
            self.assertIn('tabindex="-1"', bloque.group(0), nombre)
            self.assertIn('role="alert"', bloque.group(0), nombre)

    def test_el_resumen_enlaza_a_los_campos_invalidos(self):
        texto = (RAIZ / 'templates' / 'accounts' /
                 'register_student.html').read_text(encoding='utf-8')
        self.assertIn('href="#{{ field.id_for_label }}"', texto)

    def test_el_filtro_accesible_marca_campos_invalidos(self):
        texto = (RAIZ / 'accounts' / 'templatetags' /
                 'form_tags.py').read_text(encoding='utf-8')
        self.assertIn('aria-invalid', texto)
        self.assertIn('aria-describedby', texto)


class EstructuraPaginaTests(TestCase):
    """La página sirve la estructura accesible en la respuesta real."""

    def test_la_pagina_publica_tiene_skip_link_y_contenido(self):
        respuesta = self.client.get(reverse('jobs:job_list'))
        self.assertContains(respuesta, 'class="skip-link"')
        self.assertContains(respuesta, 'id="contenido-principal"')

    def test_la_pagina_tiene_lang_es(self):
        """§6.6 ya declara lang=es; no debe perderse."""
        respuesta = self.client.get(reverse('jobs:job_list'))
        self.assertContains(respuesta, '<html lang="es"')

    def test_no_hay_css_huerfano_fuera_de_style(self):
        """Regresion: el CSS del footer quedo fuera del <style>."""
        cuerpo = BASE.split('</head>')[0]
        self.assertNotIn('}.legal-footer', cuerpo.split('{% block extra_css %}')[0]
                         .split('</style>')[-1])


class ViewportTests(TestCase):
    """WCAG 1.4.4 — no se debe impedir el zoom."""

    def test_no_desactiva_el_zoom(self):
        """user-scalable=no es un anti-patron de la skill."""
        for ruta in (RAIZ / 'templates').rglob('*.html'):
            texto = ruta.read_text(encoding='utf-8')
            self.assertNotIn(
                'user-scalable=no', texto,
                '{} bloquea el zoom del usuario'.format(ruta.name))
