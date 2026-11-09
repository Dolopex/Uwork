"""Tests del balance.

El balance no es solo un contador: dice cuanto dinero se movio, cuanto
queda por cobrar, como se distribuyen las calificaciones y que paso
ultimamente. Estos tests comprueban que cada uno de esos numeros sale de
la base de datos y no de un numero redondo escrito a mano.
"""
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from accounts.templatetags.form_tags import cop_corto, nota
from jobs.models import Application, Job


class CalculoDelBalanceTests(TestCase):
    """Los agregados del balance."""

    def setUp(self):
        # is_email_verified=True es obligatorio: el backend de
        # autenticacion rechaza las cuentas sin verificar y force_login no
        # puede saltarselo.
        self.empleador = User.objects.create_user(
            username='emp', password='Aa12345678xyz!', rol=User.Rol.EMPLEADOR,
            email='emp@empresa.com', is_email_verified=True)
        self.estudiante = User.objects.create_user(
            username='est', password='Aa12345678xyz!', rol=User.Rol.ESTUDIANTE,
            email='est@campusuninunez.edu.co', is_email_verified=True)

    def _trabajo(self, pago, estado=Job.Estado.DISPONIBLE):
        return Job.objects.create(
            titulo='Trabajo de prueba', descripcion='Descripcion',
            pago=pago, estado=estado, creador=self.empleador,
            fecha_limite='2030-01-01')

    def _postulacion(self, trabajo, estado=Application.Estado.PENDIENTE):
        return Application.objects.create(
            usuario=self.estudiante, trabajo=trabajo, estado=estado,
            mensaje='Quiero hacerlo')

    def test_el_balance_es_publico_para_cualquier_rol(self):
        for usuario in (self.estudiante, self.empleador):
            with self.subTest(rol=usuario.rol):
                self.client.force_login(usuario)
                respuesta = self.client.get(reverse('accounts:balance'))
                self.assertEqual(respuesta.status_code, 200)

    def test_el_estudiante_ve_lo_que_ha_ganado(self):
        trabajo = self._trabajo(Decimal('250000'), Job.Estado.FINALIZADO)
        trabajo.asignado = self.estudiante
        trabajo.save()
        self.client.force_login(self.estudiante)
        respuesta = self.client.get(reverse('accounts:balance'))
        self.assertEqual(respuesta.context['total_ganado'], Decimal('250000'))
        self.assertContains(respuesta, '$250.000')

    def test_lo_que_esta_en_proceso_no_cuenta_como_ganado(self):
        """Un trabajo en curso ya tiene valor, pero no esta cobrado."""
        trabajo = self._trabajo(Decimal('120000'), Job.Estado.EN_PROCESO)
        trabajo.asignado = self.estudiante
        trabajo.save()
        self.client.force_login(self.estudiante)
        respuesta = self.client.get(reverse('accounts:balance'))
        self.assertEqual(respuesta.context['total_ganado'], 0)
        self.assertEqual(respuesta.context['en_proceso_dinero'], Decimal('120000'))

    def test_el_promedio_por_trabajo_sale_de_los_finalizados(self):
        for pago in ('100000', '300000'):
            trabajo = self._trabajo(Decimal(pago), Job.Estado.FINALIZADO)
            trabajo.asignado = self.estudiante
            trabajo.save()
        self.client.force_login(self.estudiante)
        respuesta = self.client.get(reverse('accounts:balance'))
        self.assertEqual(respuesta.context['promedio_trabajo'], Decimal('200000'))

    def test_la_tasa_de_aceptacion_del_estudiante(self):
        """Un estudiante solo puede postularse una vez a cada trabajo."""
        estados = [Application.Estado.ACEPTADA, Application.Estado.PENDIENTE,
                   Application.Estado.RECHAZADA, Application.Estado.RECHAZADA]
        for estado in estados:
            self._postulacion(self._trabajo(Decimal('50000')), estado)
        self.client.force_login(self.estudiante)
        respuesta = self.client.get(reverse('accounts:balance'))
        self.assertEqual(respuesta.context['tasa_aceptacion'], 25)

    def test_el_empleador_ve_los_candidatos_que_recibe(self):
        trabajo = self._trabajo(Decimal('50000'))
        self._postulacion(trabajo, Application.Estado.ACEPTADA)
        self._postulacion(self._trabajo(Decimal('50000')),
                          Application.Estado.PENDIENTE)
        self.client.force_login(self.empleador)
        respuesta = self.client.get(reverse('accounts:balance'))
        self.assertEqual(respuesta.context['postulaciones_recibidas'], 2)
        self.assertEqual(respuesta.context['aceptadas_recibidas'], 1)
        self.assertEqual(respuesta.context['candidatos_por_trabajo'], 1.0)

    def test_la_distribucion_de_calificaciones_cubre_la_escala(self):
        """Las cinco posiciones siempre aparecen, aunque no haya reseñas."""
        self.client.force_login(self.estudiante)
        respuesta = self.client.get(reverse('accounts:balance'))
        distribucion = respuesta.context['distribucion_calificaciones']
        self.assertEqual([d['puntos'] for d in distribucion], [5, 4, 3, 2, 1])
        self.assertEqual(sum(d['total'] for d in distribucion), 0)

    def test_el_desglose_por_categoria_no_inventa_colores(self):
        """La categoria no es un estado: el color no la codifica."""
        self._trabajo(Decimal('50000'), Job.Estado.FINALIZADO)
        self.client.force_login(self.empleador)
        respuesta = self.client.get(reverse('accounts:balance'))
        categorias = respuesta.context['categorias_data']
        self.assertTrue(categorias)
        for categoria in categorias:
            self.assertNotIn('color', categoria)

    def test_las_ventanas_mensuales_cubren_doce_meses(self):
        """Seis meses no alcanzan a cubrir un ciclo de trabajo."""
        self.client.force_login(self.estudiante)
        respuesta = self.client.get(reverse('accounts:balance'))
        self.assertEqual(len(respuesta.context['meses']), 12)
        self.assertEqual(len(respuesta.context['dinero_mes']), 12)

    def test_las_abreviaturas_de_mes_estan_en_espanol(self):
        """strftime('%b') devuelve el mes del locale del servidor."""
        self.client.force_login(self.estudiante)
        respuesta = self.client.get(reverse('accounts:balance'))
        etiquetas = [m['label'] for m in respuesta.context['meses']]
        self.assertTrue(all(len(e) <= 3 for e in etiquetas))
        self.assertIn('ene', etiquetas)
        self.assertNotIn('Jan', etiquetas)


class FormatoDeCifrasTests(TestCase):
    """Los filtros que dan formato a las cifras."""

    def test_la_calificacion_usa_coma_decimal(self):
        self.assertEqual(nota(4.5), '4,5')
        self.assertEqual(nota(5), '5,0')
        self.assertEqual(nota('xyz'), 'xyz')

    def test_el_importe_abreviado_cabe_una_etiqueta(self):
        self.assertEqual(cop_corto(380000), '$380K')
        self.assertEqual(cop_corto(1300000), '$1,3M')
        self.assertEqual(cop_corto(800), '$800')
        self.assertEqual(cop_corto(0), '$0')
        self.assertEqual(cop_corto('xyz'), 'xyz')


class EstadosVaciosDelBalanceTests(TestCase):
    """Un balance sin datos dice como se llena, no muestra ceros."""

    def test_un_usuario_sin_actividad_ve_estados_vacios(self):
        usuario = User.objects.create_user(
            username='nuevo', password='Aa12345678xyz!', rol=User.Rol.ESTUDIANTE,
            email='nuevo@campusuninunez.edu.co', is_email_verified=True)
        self.client.force_login(usuario)
        respuesta = self.client.get(reverse('accounts:balance'))
        self.assertContains(respuesta, 'Todavía no hay dinero registrado')
        self.assertContains(respuesta, 'Sin actividad en los últimos doce meses')
        self.assertContains(respuesta, 'Sin calificaciones todavía')
        self.assertContains(respuesta, 'Nada registrado todavía')
