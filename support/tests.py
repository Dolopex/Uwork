"""Tests del módulo de soporte.

Antes los tickets se creaban y nadie los leía: el estado nunca pasaba de
ABIERTO y el usuario no recibía respuesta.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from support.models import SupportTicket

User = get_user_model()


def crear_usuario(username, **kwargs):
    kwargs.setdefault('is_email_verified', True)
    return User.objects.create_user(
        username=username, password='demo1234',
        email='{}@uwork.test'.format(username), **kwargs)


class SoporteTests(TestCase):
    def setUp(self):
        self.usuario = crear_usuario('usuario', rol=User.Rol.ESTUDIANTE)
        self.staff = crear_usuario('staff')
        self.staff.is_staff = True
        self.staff.save()

    def test_el_usuario_crea_un_ticket(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.post(reverse('support:create'), {
            'tipo': 'pago',
            'descripcion': 'El trabajo está finalizado pero no me pagaron.',
        })
        self.assertEqual(respuesta.status_code, 302)
        ticket = SupportTicket.objects.get()
        self.assertEqual(ticket.reporter, self.usuario)
        self.assertEqual(ticket.estado, SupportTicket.Estado.ABIERTO)

    def test_el_panel_es_exclusivo_del_personal(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.get(reverse('support:panel_tickets'))
        self.assertEqual(respuesta.status_code, 302)

    def test_el_personal_ve_la_cola_de_tickets(self):
        SupportTicket.objects.create(reporter=self.usuario,
                                     tipo=SupportTicket.Tipo.BUG,
                                     descripcion='Algo falla')
        self.client.force_login(self.staff)
        respuesta = self.client.get(reverse('support:panel_tickets'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(list(respuesta.context['tickets'])), 1)

    def test_resolver_el_ticket_cambia_el_estado_y_guarda_la_respuesta(self):
        ticket = SupportTicket.objects.create(
            reporter=self.usuario, tipo=SupportTicket.Tipo.PAGO,
            descripcion='No me pagaron')
        self.client.force_login(self.staff)
        self.client.post(reverse('support:resolver_ticket', args=[ticket.pk]),
                         {'estado': 'resuelto',
                          'respuesta': 'Ya se revisó el saldo.'})
        ticket.refresh_from_db()
        self.assertEqual(ticket.estado, SupportTicket.Estado.RESUELTO)
        self.assertEqual(ticket.respuesta, 'Ya se revisó el saldo.')
        self.assertIsNotNone(ticket.resuelto_at)

    def test_no_se_puede_resolver_sin_respuesta(self):
        ticket = SupportTicket.objects.create(
            reporter=self.usuario, tipo=SupportTicket.Tipo.PAGO,
            descripcion='No me pagaron')
        self.client.force_login(self.staff)
        self.client.post(reverse('support:resolver_ticket', args=[ticket.pk]),
                         {'estado': 'resuelto', 'respuesta': ''})
        ticket.refresh_from_db()
        self.assertEqual(ticket.estado, SupportTicket.Estado.ABIERTO)

    def test_el_usuario_ve_la_respuesta_en_sus_tickets(self):
        ticket = SupportTicket.objects.create(
            reporter=self.usuario, tipo=SupportTicket.Tipo.PAGO,
            descripcion='No me pagaron', estado=SupportTicket.Estado.RESUELTO,
            respuesta='Ya se revisó.')
        self.client.force_login(self.usuario)
        respuesta = self.client.get(reverse('support:my_tickets'))
        self.assertContains(respuesta, 'Ya se revisó.')
