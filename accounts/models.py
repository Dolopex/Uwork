from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Rol(models.TextChoices):
        ESTUDIANTE = 'estudiante', 'Estudiante'
        EMPLEADOR = 'empleador', 'Necesito un trabajo hecho'

    # Rol
    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.EMPLEADOR)

    # Campos comunes
    foto = models.ImageField(upload_to='perfiles/', blank=True, null=True)
    cedula = models.CharField(max_length=20, blank=True, verbose_name='Documento de identidad')
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=255, blank=True, verbose_name='Ubicación / Dirección')
    fecha_nacimiento = models.DateField(null=True, blank=True)
    habilidades = models.TextField(blank=True, help_text='Separa las habilidades con comas')
    calificacion_promedio = models.DecimalField(max_digits=3, decimal_places=2, default=0)

    # Campos exclusivos estudiante
    universidad = models.CharField(max_length=200, blank=True)
    carrera = models.CharField(max_length=200, blank=True)
    semestre = models.PositiveSmallIntegerField(null=True, blank=True)
    foto_carnet = models.ImageField(upload_to='carnets/', blank=True, null=True, verbose_name='Foto del carnet estudiantil')

    # Seguridad
    pregunta_seguridad = models.CharField(max_length=255, blank=True)
    respuesta_seguridad = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    @property
    def es_estudiante(self):
        return self.rol == self.Rol.ESTUDIANTE

    def __str__(self):
        return self.get_full_name() or self.username
