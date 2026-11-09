"""Páginas públicas de documentos legales — R14 y R15.

R14 — Términos y Condiciones (Indicador: Página pública)
R15 — Política de Privacidad (Indicador: Página pública)

Ambas son públicas: deben ser accesibles sin iniciar sesión, ya que el
documento de pendientes las exige "visibles para todos los usuarios antes
del primer uso".

La fecha de actualización la declara el propio documento, no la plantilla:
un documento legal que cambia de fecha en cada visita no dice nada. Se
actualiza aquí, en un solo lugar, cuando el texto cambia.

El anexo con las decisiones que la institución tiene pendientes se puede
ocultar con el setting LEGAL_MOSTRAR_ANEXO. El texto principal se publica
siempre.
"""
from django.conf import settings
from django.shortcuts import render

ULTIMA_ACTUALIZACION = '5 de noviembre de 2026'
VERSION = '1.0'


def _contexto():
    return {
        'ultima_actualizacion': ULTIMA_ACTUALIZACION,
        'version_documento': VERSION,
        'mostrar_anexo': settings.LEGAL_MOSTRAR_ANEXO,
    }


def terminos(request):
    """R14 — Términos y Condiciones."""
    return render(request, 'legal/terminos.html', _contexto())


def privacidad(request):
    """R15 — Política de Privacidad."""
    return render(request, 'legal/privacidad.html', _contexto())
