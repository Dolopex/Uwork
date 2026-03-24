from django.db import models
from django.conf import settings


class Job(models.Model):
    class Estado(models.TextChoices):
        DISPONIBLE = 'disponible', 'Disponible'
        EN_PROCESO = 'en_proceso', 'En proceso'
        FINALIZADO = 'finalizado', 'Finalizado'

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

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    requisitos = models.TextField(blank=True, verbose_name='Requisitos')
    habilidades_requeridas = models.CharField(max_length=300, blank=True, verbose_name='Habilidades requeridas')
    pago = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.DISPONIBLE)
    categoria = models.CharField(max_length=20, choices=Categoria.choices, default=Categoria.OTRO)
    modalidad = models.CharField(max_length=20, choices=Modalidad.choices, default=Modalidad.REMOTO)
    ubicacion = models.CharField(max_length=200, blank=True, verbose_name='Ubicación')
    duracion_estimada = models.CharField(max_length=100, blank=True, verbose_name='Duración estimada')
    urgente = models.BooleanField(default=False)
    imagen = models.ImageField(upload_to='trabajos/', blank=True, null=True)
    creador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trabajos_creados')
    asignado = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='trabajos_asignados')
    fecha_limite = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Trabajo'
        verbose_name_plural = 'Trabajos'
        ordering = ['-created_at']

    def __str__(self):
        return self.titulo


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
        unique_together = ['usuario', 'trabajo']

    def __str__(self):
        return f'{self.usuario} -> {self.trabajo}'
