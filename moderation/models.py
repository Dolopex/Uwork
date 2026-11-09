"""Moderación de contenido y sanciones — §6.5.4 del documento de pendientes.

Pendientes que cubre este módulo:
  [x] Sistema de reportes por usuarios
  [x] Mecanismo de baneo temporal
  [x] Mecanismo de baneo permanente
  [x] Registro de auditoría para sanciones
  [x] Canal de apelación para usuarios sancionados

El SLA de respuesta a reportes se modela con `Reporte.plazo_respuesta` y se
vigila en la vista de moderación, que ordena los reportes vencidos primero.
"""
from django.conf import settings
from django.db import models


class MotivoReporte(models.TextChoices):
    ILEGAL = 'ilegal', 'Oferta ilegal'
    DISCRIMINACION = 'discriminacion', 'Discriminación'
    SUPLANTACION = 'suplantacion', 'Suplantación de identidad'
    DATOS_TERCEROS = 'datos_terceros', 'Publicación de datos de terceros'
    ESTAFA = 'estafa', 'Estafa o fraude'
    TRABAJO_INFANTIL = 'trabajo_infantil', 'Trabajo infantil'
    VIOLENCIA = 'violencia', 'Incite a la violencia'
    OTRO = 'otro', 'Otro'


class Reporte(models.Model):
    """Reporte de una publicación, hecho por un usuario.

    Se crea desde el botón "Reportar publicación" de cada trabajo.
    """

    class Estado(models.TextChoices):
        ABIERTO = 'abierto', 'Abierto'
        EN_REVISION = 'en_revision', 'En revisión'
        RESUELTO = 'resuelto', 'Resuelto'
        DESCARTADO = 'descartado', 'Descartado'

    class Resolucion(models.TextChoices):
        SIN_ACCION = 'sin_accion', 'Sin acción'
        RETIRADO = 'retirado', 'Contenido retirado'
        SANCIONADO = 'sancionado', 'Usuario sancionado'

    # SET_NULL, no CASCADE: si el moderador retira el contenido, el reporte y
    # su evidencia deben sobrevivir para la bitácora. El título queda copiado
    # en trabajo_titulo para no perder el contexto.
    trabajo = models.ForeignKey(
        'jobs.Job', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reportes')
    trabajo_titulo = models.CharField(
        max_length=200, blank=True, verbose_name='Título del trabajo reportado')
    # Autor del contenido reportado. Se guarda aparte del trabajo porque, si
    # el moderador retira la publicación, `trabajo` queda en NULL y sin esta
    # referencia no había a quién sancionar (P0-4: AttributeError en el
    # panel de moderación).
    contenido_autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        blank=True, related_name='contenidos_reportados',
        verbose_name='Autor del contenido reportado')
    reportante = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='reportes_realizados')
    motivo = models.CharField(max_length=30, choices=MotivoReporte.choices)
    descripcion = models.TextField(blank=True, verbose_name='Detalle')
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.ABIERTO)
    resolucion = models.CharField(
        max_length=20, choices=Resolucion.choices, blank=True)
    # SLA: se fija al crear el reporte y marca el vencimiento.
    plazo_respuesta = models.DateTimeField(null=True, blank=True)
    resuelto_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        blank=True, related_name='reportes_resueltos')
    created_at = models.DateTimeField(auto_now_add=True)
    resuelto_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['plazo_respuesta', '-created_at']
        verbose_name = 'Reporte de contenido'
        verbose_name_plural = 'Reportes de contenido'

    def __str__(self):
        return 'Reporte #{} de {}'.format(
            self.pk, self.trabajo_titulo or self.trabajo)

    @property
    def sla_vencido(self):
        """True si se pasó del plazo de respuesta y sigue abierto."""
        from django.utils import timezone

        if self.estado == self.Estado.RESUELTO or self.plazo_respuesta is None:
            return False
        return timezone.now() > self.plazo_respuesta


class Sancion(models.Model):
    """Bitácora de auditoría de sanciones — §6.5.4.

    Registro inmutable: consigna quién sancionó, a quién, cuándo, por qué y
    con qué duración. Las filas no se editan ni se borran; levantar un baneo
    genera una nueva entrada con la fecha de Levantamiento.
    """

    class Tipo(models.TextChoices):
        TEMPORAL = 'temporal', 'Baneo temporal'
        PERMANENTE = 'permanente', 'Baneo permanente'

    # SET_NULL + snapshot: la bitácora es un registro de auditoría. Con
    # CASCADE, el sancionado que borraba su cuenta desaparecía también de
    # la bitácora (P1-6). Ahora la fila sobrevive y conserva una copia del
    # username y del correo a quien se sancionó.
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        blank=True, related_name='sanciones_recibidas')
    usuario_username = models.CharField(
        max_length=150, blank=True, verbose_name='Usuario (copia)')
    usuario_email = models.CharField(
        max_length=254, blank=True, verbose_name='Correo (copia)')
    aplicada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='sanciones_aplicadas')
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    motivo = models.TextField()
    reporte = models.ForeignKey(
        Reporte, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sanciones')
    hasta = models.DateTimeField(
        null=True, blank=True, verbose_name='Vence el')
    created_at = models.DateTimeField(auto_now_add=True)
    levantada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        blank=True, related_name='sanciones_levantadas')
    levantada_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Sanción'
        verbose_name_plural = 'Sanciones'

    def __str__(self):
        return '{} a {} ({})'.format(
            self.get_tipo_display(), self.usuario_nombre, self.created_at.date())

    @property
    def usuario_nombre(self):
        """Nombre del sancionado, aunque su cuenta ya no exista."""
        if self.usuario_id and self.usuario:
            return self.usuario.get_username()
        return self.usuario_username or '(cuenta eliminada)'

    @property
    def vigente(self):
        return self.levantada_at is None


class Apelacion(models.Model):
    """Canal de apelación — §6.5.4: cómo un sancionado pide revisión."""

    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        EN_REVISION = 'en_revision', 'En revisión'
        ACEPTADA = 'aceptada', 'Apelación aceptada'
        RECHAZADA = 'rechazada', 'Apelación rechazada'

    sancion = models.ForeignKey(
        Sancion, on_delete=models.CASCADE, related_name='apelaciones')
    # SET_NULL + snapshot, igual que en Sancion: la apelación es parte de la
    # bitácora y no puede desaparecer porque el apelante borró su cuenta.
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        blank=True, related_name='apelaciones')
    usuario_username = models.CharField(
        max_length=150, blank=True, verbose_name='Usuario (copia)')
    motivo = models.TextField(verbose_name='Por qué solicitas la revisión')
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    respuesta = models.TextField(blank=True)
    resuelta_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        blank=True, related_name='apelaciones_resueltas')
    created_at = models.DateTimeField(auto_now_add=True)
    resuelta_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Apelación'
        verbose_name_plural = 'Apelaciones'

    def __str__(self):
        return 'Apelación de {}'.format(self.usuario_nombre)

    @property
    def usuario_nombre(self):
        """Nombre del apelante, aunque su cuenta ya no exista."""
        if self.usuario_id and self.usuario:
            return self.usuario.get_username()
        return self.usuario_username or '(cuenta eliminada)'

    @property
    def pendiente(self):
        return self.estado in (self.Estado.PENDIENTE, self.Estado.EN_REVISION)
