"""Tests del ciclo de vida de los trabajos.

Cubre los bugs corregidos en el Lote 1 y 2:
  - moderación previa a publicar (Términos §6)
  - pago no negativo
  - fecha límite real (un trabajo vencido no admite postulaciones)
  - aceptar postulante y finalizar trabajo exigen POST
  - máquina de estados del trabajo
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import JobForm
from .models import Application, Job

User = get_user_model()


def crear_usuario(username, **kwargs):
    # is_email_verified=True es obligatorio: el backend de autenticación
    # rechaza las cuentas sin correo confirmado.
    kwargs.setdefault('is_email_verified', True)
    return User.objects.create_user(
        username=username, password='demo1234',
        email='{}@uwork.test'.format(username), **kwargs)


class DatosBase(TestCase):
    def setUp(self):
        self.empleador = crear_usuario('empleador', rol=User.Rol.EMPLEADOR)
        self.estudiante = crear_usuario('estudiante', rol=User.Rol.ESTUDIANTE)
        self.otro = crear_usuario('otro', rol=User.Rol.ESTUDIANTE)

    def crear_trabajo(self, **kwargs):
        datos = {
            'titulo': 'Diseño de logo',
            'descripcion': 'Necesito un logo para mi emprendimiento.',
            'pago': 50000,
            'fecha_limite': timezone.localdate() + timedelta(days=7),
            'creador': self.empleador,
            'estado': Job.Estado.DISPONIBLE,
        }
        datos.update(kwargs)
        return Job.objects.create(**datos)


class ModeracionPreviaTests(DatosBase):
    """§6.5.4 / Términos §6 — el contenido no se publica sin aprobación."""

    def test_publicar_deja_el_trabajo_pendiente_de_revision(self):
        self.client.force_login(self.empleador)
        respuesta = self.client.post(reverse('jobs:job_create'), {
            'titulo': 'Redactar un ensayo',
            'descripcion': 'Ensayo de 3 páginas sobre energía.',
            'categoria': Job.Categoria.REDACCION,
            'modalidad': Job.Modalidad.REMOTO,
            'pago': '80000',
            'fecha_limite': (timezone.localdate() + timedelta(days=5)).isoformat(),
        })
        job = Job.objects.get(titulo='Redactar un ensayo')
        self.assertEqual(job.estado, Job.Estado.PENDIENTE_REVISION)
        self.assertRedirects(respuesta, reverse('jobs:job_detail',
                                                 args=[job.pk]))

    def test_el_trabajo_pendiente_no_aparece_en_el_listado_publico(self):
        self.crear_trabajo(titulo='Visible',
                            estado=Job.Estado.DISPONIBLE)
        self.crear_trabajo(titulo='No visible',
                           estado=Job.Estado.PENDIENTE_REVISION)
        respuesta = self.client.get(reverse('jobs:job_list'))
        titulos = [j.titulo for j in respuesta.context['jobs']]
        self.assertIn('Visible', titulos)
        self.assertNotIn('No visible', titulos)

    def test_el_autor_si_ve_su_trabajo_pendiente(self):
        job = self.crear_trabajo(estado=Job.Estado.PENDIENTE_REVISION)
        self.client.force_login(self.empleador)
        respuesta = self.client.get(reverse('jobs:job_detail', args=[job.pk]))
        self.assertEqual(respuesta.status_code, 200)

    def test_otro_usuario_no_ve_el_trabajo_pendiente(self):
        job = self.crear_trabajo(estado=Job.Estado.PENDIENTE_REVISION)
        self.client.force_login(self.otro)
        respuesta = self.client.get(reverse('jobs:job_detail', args=[job.pk]))
        self.assertRedirects(respuesta, reverse('jobs:job_list'))

    def test_editar_un_trabajo_aprobado_lo_devuelve_a_revision(self):
        job = self.crear_trabajo(estado=Job.Estado.DISPONIBLE)
        self.client.force_login(self.empleador)
        self.client.post(reverse('jobs:job_edit', args=[job.pk]), {
            'titulo': 'Diseño de logo v2',
            'descripcion': 'Cambio el contenido de la publicación.',
            'categoria': Job.Categoria.DISENO,
            'modalidad': Job.Modalidad.REMOTO,
            'pago': '60000',
            'fecha_limite': (timezone.localdate() + timedelta(days=6)).isoformat(),
        })
        job.refresh_from_db()
        self.assertEqual(job.estado, Job.Estado.PENDIENTE_REVISION)

    def test_el_moderador_aprueba_y_el_trabajo_se_publica(self):
        job = self.crear_trabajo(estado=Job.Estado.PENDIENTE_REVISION)
        moderador = crear_usuario('moderador')
        moderador.is_staff = True
        moderador.save()
        self.client.force_login(moderador)

        respuesta = self.client.post(
            reverse('moderation:revisar_trabajo', args=[job.pk]),
            {'decision': 'aprobar'})
        self.assertEqual(respuesta.status_code, 302)
        job.refresh_from_db()
        self.assertEqual(job.estado, Job.Estado.DISPONIBLE)

    def test_el_moderador_rechaza_con_motivo(self):
        job = self.crear_trabajo(estado=Job.Estado.PENDIENTE_REVISION)
        moderador = crear_usuario('moderador')
        moderador.is_staff = True
        moderador.save()
        self.client.force_login(moderador)

        self.client.post(reverse('moderation:revisar_trabajo', args=[job.pk]),
                         {'decision': 'rechazar', 'motivo': 'Contenido prohibido'})
        job.refresh_from_db()
        self.assertEqual(job.estado, Job.Estado.RECHAZADO)
        self.assertEqual(job.motivo_rechazo, 'Contenido prohibido')

    def test_rechazar_sin_motivo_no_cambia_el_estado(self):
        job = self.crear_trabajo(estado=Job.Estado.PENDIENTE_REVISION)
        moderador = crear_usuario('moderador')
        moderador.is_staff = True
        moderador.save()
        self.client.force_login(moderador)

        self.client.post(reverse('moderation:revisar_trabajo', args=[job.pk]),
                         {'decision': 'rechazar'})
        job.refresh_from_db()
        self.assertEqual(job.estado, Job.Estado.PENDIENTE_REVISION)


class PagoNegativoTests(DatosBase):
    """P1-3 — `min='0'` en el HTML es solo una ayuda visual."""

    def test_el_formulario_rechaza_un_pago_negativo(self):
        form = JobForm(data={
            'titulo': 'Trabajo',
            'descripcion': 'Descripción',
            'categoria': Job.Categoria.OTRO,
            'modalidad': Job.Modalidad.REMOTO,
            'pago': '-1000',
            'fecha_limite': (timezone.localdate() + timedelta(days=3)).isoformat(),
        })
        self.assertFalse(form.is_valid())
        self.assertIn('pago', form.errors)

    def test_el_formulario_acepta_un_pago_en_cero(self):
        form = JobForm(data={
            'titulo': 'Trabajo',
            'descripcion': 'Descripción',
            'categoria': Job.Categoria.OTRO,
            'modalidad': Job.Modalidad.REMOTO,
            'pago': '0',
            'fecha_limite': (timezone.localdate() + timedelta(days=3)).isoformat(),
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_el_modelo_rechaza_un_pago_negativo(self):
        job = self.crear_trabajo()
        job.pago = -100
        with self.assertRaises(ValidationError):
            job.full_clean()

    def test_la_base_de_datos_tambien_lo_impide(self):
        """El CHECK constraint cierra la puerta aunque se salte el form."""
        from django.db import IntegrityError, transaction
        job = self.crear_trabajo()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Job.objects.filter(pk=job.pk).update(pago=-100)


class FechaLimiteTests(DatosBase):
    """P1-4 — `fecha_limite` era decorativo."""

    def test_el_formulario_rechaza_una_fecha_pasada(self):
        form = JobForm(data={
            'titulo': 'Trabajo',
            'descripcion': 'Descripción',
            'categoria': Job.Categoria.OTRO,
            'modalidad': Job.Modalidad.REMOTO,
            'pago': '1000',
            'fecha_limite': (timezone.localdate() - timedelta(days=1)).isoformat(),
        })
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_limite', form.errors)

    def test_un_trabajo_vencido_no_aparece_en_el_listado(self):
        self.crear_trabajo(titulo='Vigente')
        self.crear_trabajo(titulo='Vencido',
                            fecha_limite=timezone.localdate() - timedelta(days=1))
        respuesta = self.client.get(reverse('jobs:job_list'))
        titulos = [j.titulo for j in respuesta.context['jobs']]
        self.assertNotIn('Vencido', titulos)

    def test_no_se_puede_postular_a_un_trabajo_vencido(self):
        job = self.crear_trabajo(fecha_limite=timezone.localdate()
                                 - timedelta(days=1))
        self.client.force_login(self.estudiante)
        respuesta = self.client.get(reverse('jobs:job_apply', args=[job.pk]))
        self.assertRedirects(respuesta, reverse('jobs:job_detail',
                                                 args=[job.pk]))
        self.assertFalse(Application.objects.filter(trabajo=job).exists())

    def test_el_modelo_marca_el_trabajo_como_vencido(self):
        job = self.crear_trabajo(fecha_limite=timezone.localdate()
                                 - timedelta(days=1))
        self.assertTrue(job.es_vencido)
        self.assertFalse(job.acepta_postulaciones)


class MutacionesExigenPostTests(DatosBase):
    """P0-1 — GET mutaba estado: un <img src> en un correo alcanzaba."""

    def setUp(self):
        super().setUp()
        self.job = self.crear_trabajo()
        self.postulacion = Application.objects.create(
            usuario=self.estudiante, trabajo=self.job,
            mensaje='Quiero hacerlo')
        self.client.force_login(self.empleador)

    def test_aceptar_postulante_con_get_no_hace_nada(self):
        respuesta = self.client.get(reverse('jobs:accept_applicant',
                                             args=[self.job.pk,
                                                   self.postulacion.pk]))
        self.assertEqual(respuesta.status_code, 405)
        self.postulacion.refresh_from_db()
        self.assertEqual(self.postulacion.estado, Application.Estado.PENDIENTE)
        self.job.refresh_from_db()
        self.assertEqual(self.job.estado, Job.Estado.DISPONIBLE)

    def test_aceptar_postulante_con_post_si(self):
        respuesta = self.client.post(reverse('jobs:accept_applicant',
                                              args=[self.job.pk,
                                                    self.postulacion.pk]))
        self.assertEqual(respuesta.status_code, 302)
        self.postulacion.refresh_from_db()
        self.assertEqual(self.postulacion.estado, Application.Estado.ACEPTADA)
        self.job.refresh_from_db()
        self.assertEqual(self.job.estado, Job.Estado.EN_PROCESO)
        self.assertEqual(self.job.asignado, self.estudiante)

    def test_finalizar_con_get_no_hace_nada(self):
        self.job.estado = Job.Estado.EN_PROCESO
        self.job.asignado = self.estudiante
        self.job.save()
        respuesta = self.client.get(reverse('jobs:job_finish',
                                             args=[self.job.pk]))
        self.assertEqual(respuesta.status_code, 405)
        self.job.refresh_from_db()
        self.assertEqual(self.job.estado, Job.Estado.EN_PROCESO)

    def test_finalizar_con_post_si(self):
        self.job.estado = Job.Estado.EN_PROCESO
        self.job.asignado = self.estudiante
        self.job.save()
        respuesta = self.client.post(reverse('jobs:job_finish',
                                              args=[self.job.pk]))
        self.assertEqual(respuesta.status_code, 302)
        self.job.refresh_from_db()
        self.assertEqual(self.job.estado, Job.Estado.FINALIZADO)


class MaquinaDeEstadosTests(DatosBase):
    """Un trabajo finalizado no se puede reabrir (invalidaría las reseñas)."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.empleador)

    def test_no_se_reabre_un_trabajo_finalizado(self):
        job = self.crear_trabajo(estado=Job.Estado.FINALIZADO)
        respuesta = self.client.post(reverse('jobs:job_change_status',
                                              args=[job.pk]),
                                     {'estado': Job.Estado.DISPONIBLE})
        self.assertEqual(respuesta.status_code, 302)
        job.refresh_from_db()
        self.assertEqual(job.estado, Job.Estado.FINALIZADO)

    def test_no_se_salta_la_revision_desde_disponible(self):
        job = self.crear_trabajo(estado=Job.Estado.DISPONIBLE)
        self.client.post(reverse('jobs:job_change_status', args=[job.pk]),
                         {'estado': Job.Estado.RECHAZADO})
        job.refresh_from_db()
        self.assertEqual(job.estado, Job.Estado.DISPONIBLE)

    def test_se_puede_pasar_a_en_proceso(self):
        job = self.crear_trabajo(estado=Job.Estado.DISPONIBLE)
        self.client.post(reverse('jobs:job_change_status', args=[job.pk]),
                         {'estado': Job.Estado.EN_PROCESO})
        job.refresh_from_db()
        self.assertEqual(job.estado, Job.Estado.EN_PROCESO)


class MisPostulacionesTests(DatosBase):
    """El enlace decía "mis postulaciones" pero mostraba trabajos."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.estudiante)

    def test_muestra_el_estado_de_cada_postulacion(self):
        job = self.crear_trabajo()
        postulacion = Application.objects.create(
            usuario=self.estudiante, trabajo=job, mensaje='Hola')
        respuesta = self.client.get(reverse('jobs:my_jobs'))
        self.assertIn(postulacion, list(respuesta.context['mis_postulaciones']))

    def test_el_conteo_de_completados_es_correcto(self):
        self.crear_trabajo(titulo='Terminado', asignado=self.estudiante,
                           estado=Job.Estado.FINALIZADO)
        self.crear_trabajo(titulo='En curso', asignado=self.estudiante,
                           estado=Job.Estado.EN_PROCESO)
        respuesta = self.client.get(reverse('jobs:my_jobs'))
        self.assertEqual(respuesta.context['asignados_finalizados'], 1)
        self.assertEqual(respuesta.context['asignados_en_proceso'], 1)
