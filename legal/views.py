"""Páginas públicas de documentos legales — R14 y R15.

R14 — Términos y Condiciones (Indicador: Página pública)
R15 — Política de Privacidad (Indicador: Página pública)

Ambas son públicas: deben ser accesibles sin iniciar sesión, ya que el
documento de pendientes las exige "visibles para todos los usuarios antes
del primer uso".
"""
from django.shortcuts import render


def terminos(request):
    """R14 — Términos y Condiciones."""
    return render(request, 'legal/terminos.html')


def privacidad(request):
    """R15 — Política de Privacidad."""
    return render(request, 'legal/privacidad.html')
