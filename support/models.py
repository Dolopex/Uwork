from django.db import models
from django.conf import settings


class SupportTicket(models.Model):
    class Tipo(models.TextChoices):
        BUG     = 'bug',     'Error en la app'
        USUARIO = 'usuario', 'Reportar usuario'
        PAGO    = 'pago',    'Problema con pago'
        OTRO    = 'otro',    'Otro'

    class Estado(models.TextChoices):
        ABIERTO     = 'abierto',     'Abierto'
        EN_REVISION = 'en_revision', 'En revisión'
        RESUELTO    = 'resuelto',    'Resuelto'

    reporter           = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tickets_enviados')
    tipo               = models.CharField(max_length=20, choices=Tipo.choices)
    descripcion        = models.TextField(verbose_name='Descripción del problema')
    usuario_reportado  = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reportes_recibidos',
        verbose_name='Usuario reportado (opcional)'
    )
    estado     = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ABIERTO)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Ticket de soporte'
        verbose_name_plural = 'Tickets de soporte'

    def __str__(self):
        return f'#{self.pk} {self.get_tipo_display()} — {self.reporter}'
