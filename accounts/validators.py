"""Validadores de dominio institucional — R10 (software_pendientes.txt).

R10 — Whitelist de correos institucionales
Indicador: Validación por dominio
Detalle:   El sistema debe restringir el registro a correos con dominio
           institucional verificado. Inicialmente @campusuninunez.edu.co.
"""
from django.conf import settings
from django.core.exceptions import ValidationError


def institutional_email(value):
    """Valida que el correo pertenezca a un dominio institucional permitido.

    Solo aplica a estudiantes: los empleadores (usuarios externos) se
    registran con email personal según §5 del documento de pendientes.
    """
    domain = value.rsplit('@', 1)[-1].strip().lower()
    if domain not in settings.INSTITUTIONAL_DOMAINS:
        permitidos = ', '.join('@' + d for d in settings.INSTITUTIONAL_DOMAINS)
        raise ValidationError(
            'El correo debe pertenecer a un dominio institucional ({}) para '
            'registrarte como estudiante.'.format(permitidos),
            code='dominio_no_institucional',
        )
