"""Señales de reseñas — recalcula la calificación promedio del receptor.

P1-5 — `calificacion_promedio` solo se recalculaba al *crear* una reseña.
Si el autor borraba su reseña, el promedio quedaba congelado con una
puntuación que ya no existía: reputación falsa. Con la señal, el promedio
se recalcula en cada alta y en cada borrado.
"""
from django.db.models import Avg

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Review


def recalcular_promedio(receptor_id):
    """Recalcula y guarda `calificacion_promedio` del usuario indicado."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    promedio = Review.objects.filter(receptor_id=receptor_id).aggregate(
        Avg('puntuacion'))['puntuacion__avg']
    User.objects.filter(pk=receptor_id).update(
        calificacion_promedio=promedio or 0)


@receiver(post_save, sender=Review)
def review_guardada(sender, instance, **kwargs):
    recalcular_promedio(instance.receptor_id)


@receiver(post_delete, sender=Review)
def review_eliminada(sender, instance, **kwargs):
    recalcular_promedio(instance.receptor_id)
