import uuid
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


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

    # Sanción (§6.5.4 — baneo temporal, permanente y bitácora de auditoría)
    is_banned = models.BooleanField(
        default=False, verbose_name='Cuenta sancionada')
    baneo_hasta = models.DateTimeField(
        null=True, blank=True, verbose_name='Suspensión hasta')
    motivo_baneo = models.TextField(blank=True, verbose_name='Motivo de la sanción')

    # Verificación de email (R11)
    is_email_verified = models.BooleanField(
        default=False, verbose_name='Correo verificado')
    # El token se genera bajo demanda (renovar_token_verificacion), por eso
    # es nullable: las cuentas existentes no lo tienen hasta que lo piden.
    email_verification_token = models.UUIDField(
        null=True, blank=True, editable=False, unique=True)
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    @property
    def es_estudiante(self):
        return self.rol == self.Rol.ESTUDIANTE

    def __str__(self):
        return self.get_full_name() or self.username

    # ── Verificación de email (R11) ──────────────────────────────
    EMAIL_VERIFICATION_TIMEOUT_HOURS = 48

    def renovar_token_verificacion(self):
        """Genera un token nuevo y registra cuándo se envió el correo."""
        self.email_verification_token = uuid.uuid4()
        self.email_verification_sent_at = timezone.now()
        if self.pk:
            self.save(update_fields=[
                'email_verification_token', 'email_verification_sent_at'])
        return self.email_verification_token

    @property
    def token_verificacion_expirado(self):
        """True si el enlace de verificación ya venció."""
        if self.email_verification_sent_at is None:
            return False
        limite = timezone.now() - timedelta(
            hours=self.EMAIL_VERIFICATION_TIMEOUT_HOURS)
        return self.email_verification_sent_at < limite

    def verificar_email(self):
        """Activa la cuenta tras hacer clic en el enlace del correo."""
        self.is_email_verified = True
        self.email_verification_sent_at = None
        self.save(update_fields=['is_email_verified', 'email_verification_sent_at'])

    # ── Sanción (§6.5.4) ─────────────────────────────────────────
    @property
    def baneo_vigente(self):
        """True si la sanción sigue activa.

        Un baneo sin fecha de vencimiento es permanente; uno con fecha
        deja de estar vigente cuando esa fecha pasa.
        """
        if not self.is_banned:
            return False
        if self.baneo_hasta is None:
            return True
        return timezone.now() < self.baneo_hasta

    def aplicar_baneo(self, motivo, hasta=None):
        """Sanciona la cuenta. Sin `hasta` el baneo es permanente."""
        self.is_banned = True
        self.baneo_hasta = hasta
        self.motivo_baneo = motivo
        self.save(update_fields=['is_banned', 'baneo_hasta', 'motivo_baneo'])

    def levantar_baneo(self):
        """Retira la sanción y deja la cuenta utilizable."""
        self.is_banned = False
        self.baneo_hasta = None
        self.motivo_baneo = ''
        self.save(update_fields=['is_banned', 'baneo_hasta', 'motivo_baneo'])
