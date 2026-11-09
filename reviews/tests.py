"""Tests de las reseñas y del cálculo de la calificación promedio.

P1-5 — `calificacion_promedio` solo se recalculaba al crear una reseña: si
el autor borraba su reseña, la reputación quedaba congelada con una
puntuación que ya no existía.
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from jobs.models import Job
from reviews.models import Review

User = get_user_model()


def crear_usuario(username, **kwargs):
    kwargs.setdefault('is_email_verified', True)
    return User.objects.create_user(
        username=username, password='demo1234',
        email='{}@uwork.test'.format(username), **kwargs)


class CalificacionPromedioTests(TestCase):
    def setUp(self):
        self.empleador = crear_usuario('empleador', rol=User.Rol.EMPLEADOR)
        self.estudiante = crear_usuario('estudiante', rol=User.Rol.ESTUDIANTE)
        self.job = Job.objects.create(
            titulo='Trabajo finalizado',
            descripcion='Descripción',
            pago=50000,
            fecha_limite=timezone.localdate() + timedelta(days=1),
            creador=self.empleador,
            asignado=self.estudiante,
            estado=Job.Estado.FINALIZADO,
        )

    def test_al_crear_una_resena_actualiza_el_promedio(self):
        Review.objects.create(autor=self.estudiante, receptor=self.empleador,
                              trabajo=self.job, puntuacion=5)
        self.empleador.refresh_from_db()
        self.assertEqual(float(self.empleador.calificacion_promedio), 5.0)

    def test_al_borrar_una_resena_recalcula_el_promedio(self):
        otro = crear_usuario('otro', rol=User.Rol.ESTUDIANTE)
        review = Review.objects.create(autor=self.estudiante,
                                       receptor=self.empleador,
                                       trabajo=self.job, puntuacion=5)
        Review.objects.create(autor=otro, receptor=self.empleador,
                              trabajo=self.job, puntuacion=3)
        self.empleador.refresh_from_db()
        self.assertEqual(float(self.empleador.calificacion_promedio), 4.0)

        review.delete()
        self.empleador.refresh_from_db()
        self.assertEqual(float(self.empleador.calificacion_promedio), 3.0)

    def test_al_borrar_la_ultima_resena_el_promedio_vuelve_a_cero(self):
        review = Review.objects.create(autor=self.estudiante,
                                       receptor=self.empleador,
                                       trabajo=self.job, puntuacion=4)
        review.delete()
        self.empleador.refresh_from_db()
        self.assertEqual(float(self.empleador.calificacion_promedio), 0.0)

    def test_crear_una_resena_desde_la_vista_actualiza_el_promedio(self):
        self.client.force_login(self.estudiante)
        self.client.post(reverse('reviews:create_review',
                                 args=[self.job.pk]), {'puntuacion': 4,
                                                       'comentario': 'Buen trabajo'})
        self.empleador.refresh_from_db()
        self.assertEqual(float(self.empleador.calificacion_promedio), 4.0)

    def test_crear_una_resena_notifica_al_receptor(self):
        from notifications.models import Notification
        self.client.force_login(self.estudiante)
        self.client.post(reverse('reviews:create_review',
                                 args=[self.job.pk]), {'puntuacion': 4})
        self.assertTrue(Notification.objects.filter(
            usuario=self.empleador,
            tipo=Notification.Tipo.RESENA).exists())
