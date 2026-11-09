"""Tests de los controles de seguridad de la capa de despliegue.

P0-1 — SECURE_SSL_REDIRECT sin SECURE_PROXY_SSL_HEADER provocaba un bucle
de redirección en Vercel: el edge termina TLS y reenvía por HTTP interno
con X-Forwarded-Proto, así que `is_secure()` devolvía False y la app
respondía 301 para siempre.

P0-2 — la cabecera Content-Security-Policy nunca se emitía: los settings
CSP_* existían pero ningún middleware los aplicaba.
"""
from django.test import TestCase, override_settings
from django.urls import reverse


class ContentSecurityPolicyTests(TestCase):
    """P0-2 — la CSP se emite, con nonce, y sin 'unsafe-inline' en scripts."""

    def test_la_csp_se_emite_en_cada_respuesta(self):
        respuesta = self.client.get(reverse('jobs:job_list'))
        self.assertIn('Content-Security-Policy', respuesta.headers)

    def test_la_csp_lleva_un_nonce_por_respuesta(self):
        respuesta = self.client.get(reverse('jobs:job_list'))
        csp = respuesta.headers['Content-Security-Policy']
        self.assertIn("'nonce-", csp)

    def test_dos_peticiones_tienen_nonces_distintos(self):
        primera = self.client.get(reverse('jobs:job_list'))
        segunda = self.client.get(reverse('jobs:job_list'))
        self.assertNotEqual(primera.headers['Content-Security-Policy'],
                            segunda.headers['Content-Security-Policy'])

    def test_script_src_no_permite_inline(self):
        """Sin 'unsafe-inline' los manejadores onclick quedan bloqueados."""
        respuesta = self.client.get(reverse('jobs:job_list'))
        csp = respuesta.headers['Content-Security-Policy']
        script_src = [parte for parte in csp.split(';')
                      if parte.strip().startswith('script-src')][0]
        self.assertNotIn("'unsafe-inline'", script_src)
        self.assertIn("'nonce-", script_src)

    def test_style_src_no_lleva_nonce(self):
        """Un nonce en style-src anula 'unsafe-inline' y rompe el diseño.

        La spec de CSP ignora 'unsafe-inline' cuando la lista de fuentes
        tiene un nonce o un hash. Este proyecto depende de
        'unsafe-inline' en estilos: hay un bloque <style> por plantilla
        (en base.html está todo el diseño) y cientos de atributos style=,
        que no pueden llevar nonce.
        """
        respuesta = self.client.get(reverse('jobs:job_list'))
        csp = respuesta.headers['Content-Security-Policy']
        style_src = [parte for parte in csp.split(';')
                     if parte.strip().startswith('style-src')][0]
        self.assertNotIn("'nonce-", style_src)
        self.assertIn("'unsafe-inline'", style_src)

    def test_la_pagina_tiene_estilos_inline(self):
        """Si el navegador bloquea el CSS, la app sale sin diseñar.

        Los tokens viven en static/css/style.css, pero las plantillas
        usan estilos en linea, asi que 'unsafe-inline' sigue siendo
        necesario en style-src.
        """
        respuesta = self.client.get(reverse('jobs:job_list'))
        html = respuesta.content.decode('utf-8')
        # La hoja de sistema se enlaza y trae los tokens.
        self.assertIn('/static/css/style.css', html)
        # Y las plantillas siguen usando estilos en linea.
        self.assertIn('style="', html)

    def test_el_nonce_del_html_coincide_con_el_de_la_cabecera(self):
        respuesta = self.client.get(reverse('accounts:login'))
        csp = respuesta.headers['Content-Security-Policy']
        nonce = csp.split("'nonce-")[1].split("'")[0]
        self.assertContains(respuesta, 'nonce="{}"'.format(nonce))

    def test_las_plantillas_standalone_tambien_llevan_nonce(self):
        """login.html y role_select.html no heredan de base.html."""
        for nombre in ('accounts:login', 'accounts:role_select'):
            with self.subTest(plantilla=nombre):
                respuesta = self.client.get(reverse(nombre))
                csp = respuesta.headers['Content-Security-Policy']
                nonce = csp.split("'nonce-")[1].split("'")[0]
                self.assertContains(respuesta, 'nonce="{}"'.format(nonce))


@override_settings(DEBUG=False,
                   ALLOWED_HOSTS=['testserver'],
                   SECURE_SSL_REDIRECT=True,
                   SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https'))
class RedireccionSslTests(TestCase):
    """P0-1 — detrás del proxy de Vercel no puede haber bucle de 301."""

    def test_una_peticion_con_el_proxy_https_no_se_redirige(self):
        respuesta = self.client.get('/', headers={'x-forwarded-proto': 'https'})
        self.assertEqual(respuesta.status_code, 200)

    def test_sin_la_cabecera_del_proxy_si_se_redirige(self):
        respuesta = self.client.get('/')
        self.assertEqual(respuesta.status_code, 301)
        self.assertTrue(respuesta.headers['Location'].startswith('https://'))

    def test_un_proxy_que_no_es_https_tambien_se_redirige(self):
        respuesta = self.client.get('/', headers={'x-forwarded-proto': 'http'})
        self.assertEqual(respuesta.status_code, 301)


class ManejadoresInlineTests(TestCase):
    """P0-2 — la CSP bloquea los manejadores inline: no puede quedar ninguno."""

    PLANTILLAS = (
        'templates/base.html',
        'templates/accounts/login.html',
        'templates/accounts/role_select.html',
        'templates/accounts/profile.html',
        'templates/jobs/job_list.html',
        'templates/jobs/job_detail.html',
        'templates/jobs/my_jobs.html',
        'templates/support/ticket_form.html',
    )

    def test_no_quedan_manejadores_inline_en_las_plantillas(self):
        import pathlib
        import re

        raiz = pathlib.Path(__file__).resolve().parent.parent
        patron = re.compile(r'\son(click|submit|change|load|error)=')
        for relativa in self.PLANTILLAS:
            with self.subTest(plantilla=relativa):
                texto = (raiz / relativa).read_text(encoding='utf-8')
                # Se ignoran los comentarios que mencionan los atributos.
                limpio = re.sub(r'<!--.*?-->', '', texto, flags=re.S)
                limpio = re.sub(r'//.*', '', limpio)
                self.assertIsNone(patron.search(limpio),
                                  'Hay un manejador inline en {}'.format(relativa))
