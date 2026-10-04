"""Envío del correo de verificación de email — R11.

R11 — Verificación de email
Indicador: Link de confirmación
Detalle:   Al registrarse, enviar email con token único. El usuario debe
           hacer clic antes de activar la cuenta.

En desarrollo (DEBUG=True) o sin RESEND_API_KEY configurada, el mensaje se
imprime en la consola: así el enlace de verificación es visible y testeable
sin depender de un proveedor externo. En producción, si hay RESEND_API_KEY,
se envía el correo real vía la API de Resend (compatible con Vercel
serverless, donde no hay SMTP saliente).
"""
import json
import logging
import urllib.error
import urllib.request

from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)


def _link_verificacion(token):
    """Construye el enlace absoluto de confirmación."""
    return '{}{}'.format(
        settings.SITE_URL,
        reverse('accounts:verify_email', args=[str(token)]),
    )


def enviar_email_verificacion(user):
    """Envía (o imprime) el correo con el enlace de confirmación.

    Devuelve True si el mensaje salió por un canal real, False si solo se
    imprimió en consola. No lanza excepción si el envío falla: un error de
    red no debe perder el registro del usuario.
    """
    token = user.renovar_token_verificacion()
    enlace = _link_verificacion(token)
    asunto = 'Verifica tu correo en U-Work'
    cuerpo = (
        'Hola {nombre},\n\n'
        'Bienvenido a U-Work. Para activar tu cuenta confirma tu correo '
        'electrónico haciendo clic en el siguiente enlace:\n\n'
        '  {enlace}\n\n'
        'El enlace vence en {horas} horas. Si no solicitaste este registro, '
        'puedes ignorar este mensaje.\n'
    ).format(
        nombre=user.first_name or user.username,
        enlace=enlace,
        horas=user.EMAIL_VERIFICATION_TIMEOUT_HOURS,
    )

    remitente = settings.DEFAULT_FROM_EMAIL

    # Canal real: API de Resend, si hay key configurada.
    if settings.RESEND_API_KEY and _enviar_via_resend(
            settings.RESEND_API_KEY, remitente, user.email, asunto, cuerpo):
        return True

    if settings.RESEND_API_KEY:
        logger.warning(
            'Falló el envío por Resend; se imprime el enlace en consola.')

    _imprimir_en_consola(user.email, asunto, enlace)
    return False


def _enviar_via_resend(api_key, remitente, destinatario, asunto, cuerpo):
    """POST a la API de Resend. Devuelve True si respondió 2xx."""
    payload = json.dumps({
        'from': remitente,
        'to': [destinatario],
        'subject': asunto,
        'text': cuerpo,
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.resend.com/emails',
        data=payload,
        method='POST',
        headers={
            'Authorization': 'Bearer {}'.format(api_key),
            'Content-Type': 'application/json',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return 200 <= resp.status < 300
    except (urllib.error.URLError, OSError, ValueError) as exc:
        logger.error('Error enviando email de verificación: %s', exc)
        return False


def _imprimir_en_consola(destinatario, asunto, enlace):
    """Fallback de desarrollo: deja el enlace visible en la terminal."""
    separador = '=' * 68
    print('\n' + separador)
    print('EMAIL DE VERIFICACIÓN (consola — sin RESEND_API_KEY configurada)')
    print('Para:   {}'.format(destinatario))
    print('Asunto: {}'.format(asunto))
    print('Enlace: {}'.format(enlace))
    print(separador + '\n')
