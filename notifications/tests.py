"""Tests de las notificaciones.

Lote 2 — el modelo declaraba tipos de notificación que nunca se creaban:
baneo, apelación resuelta, publicación reportada, reseña recibida y ticket
resuelto.
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from jobs.models import Job
from moderation.models import Apelacion, Reporte, Sancion
from notifications.models import Notification
from support.models import SupportTicket

User = get_user_model()


def crear_usuario(username, **kwargs):
    kwargs.setdefault('is_email_verified', True)
    return User.objects.create_user(
        username=username, password='demo1234',
        email='{}@uwork.test'.format(username), **kwargs)


def crear_staff(username):
    usuario = crear_usuario(username)
    usuario.is_staff = True
    usuario.save()
    return usuario


class NotificacionesTests(TestCase):
    def setUp(self):
        self.empleador = crear_usuario('empleador', rol=User.Rol.EMPLEADOR)
        self.estudiante = crear_usuario('estudiante', rol=User.Rol.ESTUDIANTE)
        self.staff = crear_staff('staff')
        self.job = Job.objects.create(
            titulo='Trabajo publicado',
            descripcion='Descripción',
            pago=50000,
            fecha_limite=timezone.localdate() + timedelta(days=7),
            creador=self.empleador,
            estado=Job.Estado.DISPONIBLE,
        )

    def test_la_publicacion_reportada_avisa_al_personal(self):
        self.client.force_login(self.estudiante)
        self.client.post(reverse('moderation:reportar_trabajo',
                                 args=[self.job.pk]),
                         {'motivo': 'estafa', 'descripcion': 'Es una estafa.'})
        self.assertTrue(Notification.objects.filter(
            usuario=self.staff,
            tipo=Notification.Tipo.REPORTE).exists())

    def test_el_baneo_notifica_al_sancionado(self):
        reporte = Reporte.objects.create(
            trabajo=self.job, trabajo_titulo=self.job.titulo,
            contenido_autor=self.empleador, reportante=self.estudiante,
            motivo='estafa')
        self.client.force_login(self.staff)
        self.client.post(reverse('moderation:resolver_reporte',
                                 args=[reporte.pk]),
                         {'accion': 'sancionar', 'tipo_sancion': 'permanente',
                          'motivo_sancion': 'Contenido ilegal'})
        self.assertTrue(Notification.objects.filter(
            usuario=self.empleador,
            tipo=Notification.Tipo.BANNEO).exists())

    def test_la_apelacion_resuelta_notifica_al_apelante(self):
        sancion = Sancion.objects.create(
            usuario=self.empleador, usuario_username=self.empleador.username,
            aplicada_por=self.staff, tipo=Sancion.Tipo.PERMANENTE,
            motivo='Prueba')
        apelacion = Apelacion.objects.create(
            sancion=sancion, usuario=self.empleador,
            usuario_username=self.empleador.username,
            motivo='No corresponde')

        self.client.force_login(self.staff)
        self.client.post(reverse('moderation:resolver_apelacion',
                                 args=[apelacion.pk]),
                         {'decision': 'aceptar',
                          'respuesta': 'Se levanta el baneo.'})
        self.assertTrue(Notification.objects.filter(
            usuario=self.empleador,
            tipo=Notification.Tipo.APELACION).exists())

    def test_el_ticket_resuelto_notifica_al_usuario(self):
        ticket = SupportTicket.objects.create(
            reporter=self.estudiante, tipo=SupportTicket.Tipo.PAGO,
            descripcion='No me llegó el pago.')
        self.client.force_login(self.staff)
        self.client.post(reverse('support:resolver_ticket',
                                 args=[ticket.pk]),
                         {'estado': 'resuelto',
                          'respuesta': 'Revisamos el saldo.'})
        self.assertTrue(Notification.objects.filter(
            usuario=self.estudiante,
            tipo=Notification.Tipo.TICKET).exists())

    def test_la_revision_de_una_publicacion_notifica_al_autor(self):
        job = Job.objects.create(
            titulo='Pendiente', descripcion='Descripción', pago=1000,
            fecha_limite=timezone.localdate() + timedelta(days=3),
            creador=self.empleador, estado=Job.Estado.PENDIENTE_REVISION)
        self.client.force_login(self.staff)
        self.client.post(reverse('moderation:revisar_trabajo', args=[job.pk]),
                         {'decision': 'aprobar'})
        self.assertTrue(Notification.objects.filter(
            usuario=self.empleador,
            tipo=Notification.Tipo.APROBACION).exists())

    def test_el_contador_de_no_leidas_refleja_las_nuevas(self):
        Notification.objects.create(
            usuario=self.empleador, tipo=Notification.Tipo.BANNEO,
            mensaje='Sanción')
        self.client.force_login(self.empleador)
        respuesta = self.client.get(reverse('jobs:job_list'))
        self.assertEqual(respuesta.context['notif_count'], 1)
