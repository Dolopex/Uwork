from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from jobs.models import Job


class Review(models.Model):
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_hechas')
    receptor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_recibidas')
    trabajo = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='reviews')
    puntuacion = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Calificación'
        verbose_name_plural = 'Calificaciones'
        unique_together = ['autor', 'receptor', 'trabajo']

    def __str__(self):
        return f'{self.autor} -> {self.receptor}: {self.puntuacion}⭐'
