"""Content-Security-Policy con nonce por request — §6.5.3.

El proyecto tiene dos problemas que esta pieza resuelve:

1. Los settings `CSP_*` existían pero ningún middleware los aplicaba: la
   cabecera `Content-Security-Policy` nunca se emitía.
2. `script-src` sin `'unsafe-inline'` rompe la aplicación si hay manejadores
   inline (`onclick`, `onsubmit`, `onchange`) o etiquetas `<script>` sin
   nonce. Por eso el nonce se genera por request y las plantillas lo
   referencia con `nonce="{{ csp_nonce }}"`.

El nonce se genera con `secrets.token_urlsafe`, que es criptográficamente
aleatorio, y dura lo que dura el request: nunca se reutiliza entre
respuestas.
"""
import secrets

from django.conf import settings

#: Cabeceras de la CSP y el setting que las define.
_DIRECTIVAS = (
    ('default-src', 'CSP_DEFAULT_SRC'),
    ('script-src', 'CSP_SCRIPT_SRC'),
    ('style-src', 'CSP_STYLE_SRC'),
    ('font-src', 'CSP_FONT_SRC'),
    ('img-src', 'CSP_IMG_SRC'),
    ('connect-src', 'CSP_CONNECT_SRC'),
    ('frame-ancestors', 'CSP_FRAME_ANCESTORS'),
    ('object-src', 'CSP_OBJECT_SRC'),
    ('base-uri', 'CSP_BASE_URI'),
    ('form-action', 'CSP_FORM_ACTION'),
)


def construir_csp(nonce):
    """Arma el valor de la cabecera Content-Security-Policy.

    El nonce se inyecta SOLO en `script-src`: es la única fuente de
    JavaScript propio de la aplicación y lo que impide ejecutar un
    `<script>` inyectado.

    En `style-src` NO debe ir nonce. La razón es la spec de CSP: cuando una
    lista de fuentes contiene un nonce o un hash, `'unsafe-inline'` se
    ignora. Y este proyecto necesita `'unsafe-inline'` en estilos: hay un
    bloque `<style>` por plantilla (en base.html está todo el diseño de la
    app, líneas 22-742) y 673 atributos `style=` repartidos por las
    plantillas. Un atributo `style=` no puede llevar nonce, así que ponerlo
    en style-src no daba ninguna protección y rompía todos los estilos.
    """
    partes = []
    for directiva, nombre_setting in _DIRECTIVAS:
        valores = list(getattr(settings, nombre_setting, []) or [])
        if directiva == 'script-src' and nonce:
            valores.insert(0, "'nonce-{}'".format(nonce))
        if not valores:
            continue
        partes.append('{} {}'.format(directiva, ' '.join(valores)))
    return '; '.join(partes)


class CSPNonceMiddleware:
    """Genera un nonce por request y emite la cabecera CSP."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.csp_nonce = secrets.token_urlsafe(16)
        response = self.get_response(request)
        if getattr(settings, 'CSP_ENABLED', False):
            response['Content-Security-Policy'] = construir_csp(request.csp_nonce)
        return response
