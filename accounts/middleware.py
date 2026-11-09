"""Middlewares de seguridad declarados en §6.5.3 del documento de pendientes.

- BannedUserMiddleware: cierre de sesión forzada para usuarios baneados.
- RateLimitMiddleware: límite de peticiones en endpoints sensibles.

Ambos se activan desde settings.MIDDLEWARE.
"""
import time

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import redirect


def _clave_por_ip(request, sufijo):
    """Clave de caché por IP. Detrás de proxy se usa X-Forwarded-For."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    ip = xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR', '')
    return 'rl:{}:{}'.format(ip, sufijo)


class BannedUserMiddleware:
    """§6.5.3 — 'Mecanismo de force-logout para usuarios baneados'.

    Si el usuario en sesión está baneado, se le cierra la sesión en el
    siguiente request y se le informa del motivo. También cubre el baneo
    temporal: cuando expira, el usuario vuelve a tener acceso sin que nadie
    tenga que reactivar su cuenta a mano.

    Excepción: el canal de apelación. Sin ella el sancionado quedaba en un
    callejón sin salida: el middleware cerraba la sesión en cada request,
    así que ni siquiera alcanzaba la vista para apelar (P0-3).
    """

    #: Rutas que un usuario sancionado sí puede visitar.
    RUTAS_PERMITIDAS = (
        '/moderacion/apelacion/',
        '/moderacion/apelaciones/mias/',
        '/accounts/logout/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        usuario = getattr(request, 'user', None)
        if usuario is not None and usuario.is_authenticated:
            if getattr(usuario, 'is_banned', False):
                if usuario.baneo_vigente:
                    if self._ruta_permitida(request.path):
                        return self.get_response(request)
                    motivo = usuario.motivo_baneo or ''
                    expiracion = usuario.baneo_hasta
                    logout(request)
                    messages.error(
                        request,
                        'Tu cuenta fue suspendida. {}'.format(motivo))
                    if expiracion:
                        messages.error(
                            request,
                            'La suspensión vence el {}.'.format(
                                expiracion.strftime('%d/%m/%Y %H:%M')),
                        )
                    messages.info(
                        request,
                        'Si la sanción no corresponde, apela desde el canal '
                        'de revisión.')
                    return redirect(settings.LOGIN_URL)

                # El baneo temporal ya venció: limpiar los campos para que la
                # cuenta quede utilizable sin intervención manual.
                usuario.levantar_baneo()
        return self.get_response(request)

    def _ruta_permitida(self, path):
        return any(path.startswith(prefijo)
                   for prefijo in self.RUTAS_PERMITIDAS)


class RateLimitMiddleware:
    """§6.5.3 — 'Rate-limiting en endpoints sensibles'.

    Limita por IP y por ventana temporal, usando la caché de Django. El
    límite de 429 se responde con Retry-After para clientes y con una
    redirección al login cuando la ruta es la de inicio de sesión, para que
    un usuario legítimo bloqueado no quede en una pantalla de error cruda.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not settings.RATE_LIMIT_ENABLED or request.method == 'GET':
            return self.get_response(request)

        regla = self._regla_para(request.path)
        if regla is None:
            return self.get_response(request)

        ventana = regla['window']
        maximo = regla['limit']
        clave = _clave_por_ip(request, request.path)

        intentos = cache.get(clave)
        if intentos is None:
            intentos = []
        ahora = time.time()
        intentos = [t for t in intentos if ahora - t < ventana]
        intentos.append(ahora)
        cache.set(clave, intentos, timeout=ventana)

        if len(intentos) > maximo:
            espera = int(ventana - (ahora - min(intentos))) + 1
            if request.path.rstrip('/').endswith('login'):
                messages.error(
                    request,
                    'Demasiados intentos de inicio de sesión. Espera {} '
                    'minutos antes de volver a intentarlo.'.format(
                        max(1, espera // 60)),
                )
                return redirect(settings.LOGIN_URL)
            respuesta = HttpResponse(
                'Demasiadas solicitudes. Intenta de nuevo en {} segundos.'.format(
                    espera),
                status=429,
                content_type='text/plain; charset=utf-8',
            )
            respuesta['Retry-After'] = str(espera)
            return respuesta

        return self.get_response(request)

    def _regla_para(self, path):
        for prefijo, regla in settings.RATE_LIMITS.items():
            if path.startswith(prefijo):
                return regla
        return None
