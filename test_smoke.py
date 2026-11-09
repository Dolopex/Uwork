"""Smoke test de las páginas que cambiaron en el Lote 1 y 2.

No comprueba contenido: comprueba que ninguna vista revienta. Un 500 en
cualquiera de estas pantallas es un fallo de entrega.
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from jobs.models import Application, Job
from moderation.models import Apelacion, Reporte, Sancion
from support.models import SupportTicket

User = get_user_model()


def crear_usuario(username, rol=User.Rol.ESTUDIANTE, staff=False):
    usuario = User.objects.create_user(
        username=username, password='Aa12345678xyz!',
        email='{}@uwork.test'.format(username), is_email_verified=True,
        rol=rol)
    if staff:
        usuario.is_staff = True
        usuario.save()
    return usuario


class SmokeTest(TestCase):
    def setUp(self):
        self.empleador = crear_usuario('empleador', User.Rol.EMPLEADOR)
        self.estudiante = crear_usuario('estudiante')
        self.staff = crear_usuario('staff', staff=True)
        self.job = Job.objects.create(
            titulo='Trabajo', descripcion='Descripción', pago=50000,
            fecha_limite=timezone.localdate() + timedelta(days=7),
            creador=self.empleador, estado=Job.Estado.DISPONIBLE)
        self.pendiente = Job.objects.create(
            titulo='En revisión', descripcion='Descripción', pago=50000,
            fecha_limite=timezone.localdate() + timedelta(days=7),
            creador=self.empleador, estado=Job.Estado.PENDIENTE_REVISION)
        self.rechazado = Job.objects.create(
            titulo='Rechazado', descripcion='Descripción', pago=50000,
            fecha_limite=timezone.localdate() + timedelta(days=7),
            creador=self.empleador, estado=Job.Estado.RECHAZADO,
            motivo_rechazo='Contenido prohibido')
        self.aplicacion = Application.objects.create(
            usuario=self.estudiante, trabajo=self.job, mensaje='Hola')
        self.job_libre = Job.objects.create(
            titulo='Sin postulaciones', descripcion='Descripción', pago=50000,
            fecha_limite=timezone.localdate() + timedelta(days=7),
            creador=self.empleador, estado=Job.Estado.DISPONIBLE)
        self.reporte = Reporte.objects.create(
            trabajo=self.job, trabajo_titulo=self.job.titulo,
            contenido_autor=self.empleador, reportante=self.estudiante,
            motivo='ilegal')
        self.sancion = Sancion.objects.create(
            usuario=self.empleador, usuario_username=self.empleador.username,
            aplicada_por=self.staff, tipo=Sancion.Tipo.PERMANENTE,
            motivo='Prueba')
        self.apelacion = Apelacion.objects.create(
            sancion=self.sancion, usuario=self.empleador,
            usuario_username=self.empleador.username, motivo='Error')
        self.ticket = SupportTicket.objects.create(
            reporter=self.estudiante, tipo=SupportTicket.Tipo.PAGO,
            descripcion='No me pagaron')

    def test_paginas_publicas(self):
        for nombre in ('jobs:job_list', 'accounts:role_select',
                       'accounts:login', 'legal:terminos', 'legal:privacidad'):
            with self.subTest(pagina=nombre):
                respuesta = self.client.get(reverse(nombre))
                self.assertEqual(respuesta.status_code, 200)

    def test_paginas_del_empleador(self):
        self.client.force_login(self.empleador)
        for nombre in ('jobs:my_jobs', 'jobs:job_create',
                       'accounts:balance', 'accounts:profile'):
            with self.subTest(pagina=nombre):
                respuesta = self.client.get(reverse(nombre))
                self.assertEqual(respuesta.status_code, 200)

    def test_paginas_del_estudiante(self):
        self.client.force_login(self.estudiante)
        for nombre in ('jobs:my_jobs', 'support:create',
                       'support:my_tickets', 'notifications:list'):
            with self.subTest(pagina=nombre):
                respuesta = self.client.get(reverse(nombre))
                self.assertEqual(respuesta.status_code, 200)
        respuesta = self.client.get(
            reverse('jobs:job_apply', args=[self.job_libre.pk]))
        self.assertEqual(respuesta.status_code, 200)

    def test_detalles_de_trabajo_en_cada_estado(self):
        for job in (self.job, self.pendiente, self.rechazado):
            with self.subTest(trabajo=job.estado):
                self.client.force_login(self.empleador)
                respuesta = self.client.get(
                    reverse('jobs:job_detail', args=[job.pk]))
                self.assertEqual(respuesta.status_code, 200)

    def test_paneles_del_personal(self):
        self.client.force_login(self.staff)
        for nombre in ('moderation:panel_reportes',
                       'moderation:panel_publicaciones',
                       'moderation:apelaciones', 'moderation:bitacora',
                       'support:panel_tickets'):
            with self.subTest(panel=nombre):
                respuesta = self.client.get(reverse(nombre))
                self.assertEqual(respuesta.status_code, 200)

    def test_canal_de_apelacion(self):
        self.client.force_login(self.empleador)
        for nombre in ('moderation:apelacion_crear',
                       'moderation:mis_apelaciones'):
            with self.subTest(pagina=nombre):
                respuesta = self.client.get(reverse(nombre))
                self.assertEqual(respuesta.status_code, 200)

    def test_paginas_de_postulantes_y_soporte(self):
        self.client.force_login(self.empleador)
        respuesta = self.client.get(
            reverse('jobs:job_applicants', args=[self.job.pk]))
        self.assertEqual(respuesta.status_code, 200)

    def test_todas_las_plantillas_reciben_el_nonce(self):
        """Ninguna plantilla que extienda base.html puede quedar sin él."""
        import pathlib
        import re

        raiz = pathlib.Path(__file__).resolve().parent.parent
        plantillas = list((raiz / 'templates').rglob('*.html'))
        for ruta in plantillas:
            texto = ruta.read_text(encoding='utf-8')
            if '<script' not in texto:
                continue
            if "{% extends" not in texto and "{% include" not in texto:
                # Plantillas independientes: el nonce tiene que ir explícito.
                for etiqueta in re.findall(r'<script[^>]*>', texto):
                    if 'src=' not in etiqueta:
                        self.assertIn('nonce=', etiqueta,
                                      '{} sin nonce'.format(ruta))

    def test_el_nonce_del_html_coincide_en_todas_las_paginas(self):
        """Cada <script> inline de la página lleva el nonce de la cabecera.

        Si no coinciden, el navegador bloquea el script y la página queda
        a medio funcionar.
        """
        import re

        self.client.force_login(self.staff)
        paginas = [
            reverse('jobs:job_list'),
            reverse('jobs:my_jobs'),
            reverse('jobs:job_detail', args=[self.job.pk]),
            reverse('moderation:panel_reportes'),
            reverse('moderation:panel_publicaciones'),
            reverse('moderation:apelaciones'),
            reverse('moderation:bitacora'),
            reverse('moderation:apelacion_crear'),
            reverse('moderation:mis_apelaciones'),
            reverse('support:panel_tickets'),
            reverse('support:create'),
            reverse('notifications:list'),
            reverse('accounts:profile'),
        ]
        for url in paginas:
            with self.subTest(url=url):
                respuesta = self.client.get(url)
                self.assertEqual(respuesta.status_code, 200)
                csp = respuesta.headers.get('Content-Security-Policy', '')
                self.assertTrue(csp, 'sin cabecera CSP en {}'.format(url))
                nonce = csp.split("'nonce-")[1].split("'")[0]
                html = respuesta.content.decode('utf-8')
                for etiqueta in re.findall(r'<script[^>]*>', html):
                    if 'src=' in etiqueta:
                        continue
                    self.assertIn(
                        'nonce="{}"'.format(nonce), etiqueta,
                        'script sin el nonce correcto en {}'.format(url))

    def test_ninguna_pagina_emitida_tiene_manejadores_inline(self):
        import re

        self.client.force_login(self.empleador)
        paginas = [reverse('jobs:job_list'),
                   reverse('jobs:job_detail', args=[self.job.pk]),
                   reverse('jobs:my_jobs'),
                   reverse('accounts:profile')]
        patron = re.compile(r'\son(click|submit|change)=')
        for url in paginas:
            with self.subTest(url=url):
                html = self.client.get(url).content.decode('utf-8')
                # Los comentarios que nombran los atributos no cuentan.
                limpio = re.sub(r'<!--.*?-->', '', html, flags=re.S)
                limpio = re.sub(r'//[^\n]*', '', limpio)
                limpio = re.sub(r'/\*.*?\*/', '', limpio, flags=re.S)
                self.assertIsNone(patron.search(limpio),
                                  'manejador inline en {}'.format(url))
