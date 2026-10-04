"""Validadores de archivos subidos — §6.5.3 del documento de pendientes.

Pendiente declarado: "Validación MIME y de tamaño real en uploads".

Dos capas:
  1. ContentType declarado en el formulario (rápido, se puede falsear).
  2. Verificación real de la firma binaria del archivo y de su tamaño.

Ambas se aplican: el content-type solo no es suficiente porque el cliente
envía el que quiere.
"""
import os

from django.conf import settings
from django.core.exceptions import ValidationError

# Firmas binarias (magic numbers) de los formatos permitidos.
FIRMAS = {
    b'\xff\xd8\xff': 'image/jpeg',
    b'\x89PNG\r\n\x1a\n': 'image/png',
}


def _cabecera(archivo, cantidad=16):
    """Lee los primeros bytes sin consumirlos y restores el cursor."""
    posicion = archivo.tell()
    try:
        archivo.seek(0)
        datos = archivo.read(cantidad)
    finally:
        archivo.seek(posicion)
    return datos


def validar_imagen(archivo):
    """Valida tamaño real, extensión y tipo MIME real de una imagen."""
    if not archivo:
        return

    _validar_tamano(archivo)
    _validar_extension(archivo)
    _validar_mime(archivo)


def _validar_tamano(archivo):
    """El peso real del archivo, no el declarado en el formulario."""
    tamano = getattr(archivo, 'size', None)
    if tamano is None:
        try:
            tamano = os.path.getsize(archivo.path)
        except (OSError, ValueError, AttributeError):
            return

    maximo = settings.UPLOAD_MAX_SIZE_MB * 1024 * 1024
    if tamano > maximo:
        raise ValidationError(
            'La imagen supera el tamaño máximo de {} MB.'.format(
                settings.UPLOAD_MAX_SIZE_MB),
            code='archivo_muy_grande',
        )
    if tamano == 0:
        raise ValidationError('El archivo está vacío.', code='archivo_vacio')


def _validar_extension(archivo):
    nombre = (getattr(archivo, 'name', '') or '').lower()
    extension = os.path.splitext(nombre)[1]
    permitidas = settings.UPLOAD_ALLOWED_EXTENSIONS
    if extension and extension not in permitidas:
        raise ValidationError(
            'Formato no permitido. Usa: {}.'.format(
                ', '.join(permitidas)),
            code='extension_no_permitida',
        )


def _validar_mime(archivo):
    """Comprueba el tipo real por firma binaria y contra el permitido."""
    cabecera = _cabecera(archivo)
    if not cabecera:
        raise ValidationError('El archivo está vacío.', code='archivo_vacio')

    # WebP: "RIFF....WEBP"
    if cabecera[:4] == b'RIFF' and cabecera[8:12] == b'WEBP':
        mime_real = 'image/webp'
    else:
        mime_real = None
        for firma, mime in FIRMAS.items():
            if cabecera.startswith(firma):
                mime_real = mime
                break

    if mime_real is None:
        raise ValidationError(
            'El contenido del archivo no es una imagen válida '
            '(se esperaba JPEG, PNG o WebP).',
            code='mime_invalido',
        )

    if mime_real not in settings.UPLOAD_ALLOWED_MIME:
        raise ValidationError(
            'Tipo de imagen no permitido: {}.'.format(mime_real),
            code='mime_no_permitido',
        )

    # El content-type declarado no puede contradecir la firma real.
    declarado = (getattr(archivo, 'content_type', '') or '').lower()
    if declarado and declarado != mime_real:
        raise ValidationError(
            'El tipo declarado ({}) no coincide con el contenido real '
            '({}).'.format(declarado, mime_real),
            code='mime_engañoso',
        )
