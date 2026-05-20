from django.db import models
from django.conf import settings


class Notification(models.Model):
    class Tipo(models.TextChoices):
        POSTULACION = 'postulacion', 'Nueva postulación'
        ACEPTADO    = 'aceptado',    'Postulación aceptada'
        RECHAZADO   = 'rechazado',   'Postulación rechazada'
        FINALIZADO  = 'finalizado',  'Trabajo finalizado'
        RESENA      = 'resena',      'Nueva reseña'
        SISTEMA     = 'sistema',     'Sistema'

    usuario    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notificaciones')
    tipo       = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.SISTEMA)
    mensaje    = models.CharField(max_length=300)
    link       = models.CharField(max_length=300, blank=True)
    leida      = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'

    def __str__(self):
        return f'{self.usuario} — {self.get_tipo_display()}'
