"""Servicio de supresión de cuenta — R16.

R16 — Mecanismo "Eliminar mi cuenta"
Detalle:   CRÍTICO para el cumplimiento del artículo 17 de la Ley 1581 de
           2012 (derecho de supresión).

Django borra las filas de la base de datos en cascada, pero NO los archivos
físicos subidos a MEDIA_ROOT. Para que la supresión sea real, hay que
eliminar también las imágenes del usuario y de los trabajos que publicó.
"""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def eliminar_archivos_de_usuario(usuario,include_trabajos=True):
    """Borra del disco los archivos de MEDIA_ROOT asociados al usuario.

    Devuelve la cantidad de archivos eliminados. Los errores por archivo se
    registran pero no interrumpen el borrado: el derecho de supresión no
    debe fallar por un fichero huérfano.
    """
    borrados = 0

    # Fotos del perfil y del carné.
    for campo in ('foto', 'foto_carnet'):
        archivo = getattr(usuario, campo, None)
        borrados += _borrar_archivo(archivo)

    if not include_trabajos:
        return borrados

    from jobs.models import Job

    for trabajo in Job.objects.filter(creador=usuario):
        borrados += _borrar_archivo(trabajo.imagen)

    return borrados


def _borrar_archivo(campo):
    """Elimina un ImageField/Field. Devuelve 1 si lo borró, 0 si no había."""
    if not campo:
        return 0
    try:
        nombre = campo.name
    except (ValueError, AttributeError):
        return 0
    if not nombre:
        return 0

    ruta = _ruta_absoluta(nombre)
    if not ruta:
        return 0
    try:
        import os
        if os.path.isfile(ruta):
            os.remove(ruta)
            return 1
    except OSError as exc:
        logger.warning('No se pudo eliminar el archivo %s: %s', ruta, exc)
    return 0


def _ruta_absoluta(nombre_relativo):
    """Resuelve un nombre de MEDIA_ROOT y lo mantiene dentro de MEDIA_ROOT.

    La comprobación de prefijo evita que un nombre con '..' permita borrar
    un archivo fuera del directorio de medios.
    """
    import os

    raiz = os.path.abspath(settings.MEDIA_ROOT)
    destino = os.path.abspath(os.path.join(raiz, nombre_relativo))
    if os.path.commonpath([raiz, destino]) != raiz:
        logger.warning('Ruta de media fuera de MEDIA_ROOT, se omite: %s',
                       nombre_relativo)
        return None
    return destino
