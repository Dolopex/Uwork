from decimal import Decimal

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone


class Job(models.Model):
    class Estado(models.TextChoices):
        # Moderación previa a publicar — §6.5.4 / Términos §6.
        PENDIENTE_REVISION = 'pendiente_revision', 'Pendiente de revisión'
        DISPONIBLE = 'disponible', 'Disponible'
        EN_PROCESO = 'en_proceso', 'En proceso'
        FINALIZADO = 'finalizado', 'Finalizado'
        RECHAZADO = 'rechazado', 'Rechazado'

    class Categoria(models.TextChoices):
        ACADEMICO = 'academico', 'Académico'
        TECNOLOGIA = 'tecnologia', 'Tecnología'
        DISENO = 'diseno', 'Diseño'
        REDACCION = 'redaccion', 'Redacción'
        TRADUCCION = 'traduccion', 'Traducción'
        OTRO = 'otro', 'Otro'

    class Modalidad(models.TextChoices):
        PRESENCIAL = 'presencial', 'Presencial'
        REMOTO = 'remoto', 'Remoto'
        HIBRIDO = 'hibrido', 'Híbrido'

    #: Estados en los que el trabajo es visible para el público.
    PUBLICOS = (Estado.DISPONIBLE, Estado.EN_PROCESO, Estado.FINALIZADO)

    #: Estados en los que el trabajo todavía acepta postulaciones.
    ACEPTAN_POSTULACIONES = (Estado.DISPONIBLE,)

    #: Máquina de estados. Evita reabrir un trabajo finalizado (lo que
    #: invalidaría las reseñas ya dadas) y evita saltarse la revisión.
    TRANSICIONES = {
        Estado.PENDIENTE_REVISION: {Estado.DISPONIBLE, Estado.RECHAZADO},
        Estado.DISPONIBLE: {
            Estado.EN_PROCESO, Estado.FINALIZADO, Estado.PENDIENTE_REVISION,
        },
        Estado.EN_PROCESO: {Estado.FINALIZADO},
        Estado.FINALIZADO: set(),
        Estado.RECHAZADO: {Estado.PENDIENTE_REVISION},
    }

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    requisitos = models.TextField(blank=True, verbose_name='Requisitos')
    habilidades_requeridas = models.CharField(max_length=300, blank=True, verbose_name='Habilidades requeridas')
    # El pago no puede ser negativo: min='0' en el HTML es solo una ayuda
    # visual y un POST directo lo esquivaba (P1-3).
    pago = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'), 'El pago no puede ser negativo.')])
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.PENDIENTE_REVISION)
    categoria = models.CharField(max_length=20, choices=Categoria.choices, default=Categoria.OTRO)
    modalidad = models.CharField(max_length=20, choices=Modalidad.choices, default=Modalidad.REMOTO)
    ubicacion = models.CharField(max_length=200, blank=True, verbose_name='Ubicación')
    duracion_estimada = models.CharField(max_length=100, blank=True, verbose_name='Duración estimada')
    urgente = models.BooleanField(default=False)
    imagen = models.ImageField(upload_to='trabajos/', blank=True, null=True)
    creador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trabajos_creados')
    asignado = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='trabajos_asignados')
    fecha_limite = models.DateField()
    # Motivo del rechazo en la moderación previa a publicar.
    motivo_rechazo = models.TextField(blank=True, verbose_name='Motivo del rechazo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Trabajo'
        verbose_name_plural = 'Trabajos'
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(pago__gte=Decimal('0')),
                name='jobs_job_pago_no_negativo',
            ),
        ]

    def __str__(self):
        return self.titulo

    # ── Reglas de negocio ────────────────────────────────────────

    @property
    def es_vencido(self):
        """True si la fecha límite ya pasó."""
        return self.fecha_limite < timezone.localdate()

    @property
    def visible(self):
        """True si el trabajo puede verse en el listado público.

        Un trabajo pendiente de moderación o rechazado no es público: solo
        lo ve su autor y el personal de moderación.
        """
        return self.estado in self.PUBLICOS

    @property
    def acepta_postulaciones(self):
        """True si el trabajo admite postulaciones nuevas."""
        return (self.estado in self.ACEPTAN_POSTULACIONES
                and not self.es_vencido)

    def puede_transicionar_a(self, nuevo_estado):
        """True si el cambio de estado está permitido por la máquina."""
        permitidos = self.TRANSICIONES.get(self.estado, set())
        return nuevo_estado in permitidos


class Application(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        ACEPTADA = 'aceptada', 'Aceptada'
        RECHAZADA = 'rechazada', 'Rechazada'

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='postulaciones')
    trabajo = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='postulaciones')
    mensaje = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Postulación'
        verbose_name_plural = 'Postulaciones'
        ordering = ['-created_at']
        unique_together = ['usuario', 'trabajo']

    def __str__(self):
        return f'{self.usuario} -> {self.trabajo}'
