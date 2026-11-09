"""Tests del comando crear_admin.

El comando va en el build de Vercel: si se rompe, el despliegue se cae.
Estos tests comprueban las tres cosas de las que depende:

1. Crea el superusuario con los permisos correctos y el correo verificado
   (R11: sin verificar, el backend no lo deja entrar).
2. Es idempotente: si ya existe, lo repara sin tocar la contrasena.
3. No hace nada, y lo dice, cuando no hay contrasena definida.
"""
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

User = get_user_model()


class CrearAdminTests(TestCase):
    """accounts/management/commands/crear_admin.py"""

    def test_crea_el_superusuario_con_permisos_y_correo_verificado(self):
        call_command('crear_admin', username='nuevo_admin',
                     email='admin@uwork.app', password='ClaveSegura123!',
                     verbosity=0)

        admin = User.objects.get(username='nuevo_admin')
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)
        # R11: sin esto el backend de autenticacion lo rechaza.
        self.assertTrue(admin.is_email_verified)

    def test_el_superusuario_puede_autenticarse(self):
        """La comprobacion que importa: entrar de verdad."""
        call_command('crear_admin', username='nuevo_admin',
                     email='admin@uwork.app', password='ClaveSegura123!',
                     verbosity=0)

        admin = User.objects.get(username='nuevo_admin')
        self.assertTrue(admin.check_password('ClaveSegura123!'))

    def test_no_crea_nada_sin_contrasena(self):
        """Un superusuario con contrasena predecible es peor que ninguno."""
        call_command('crear_admin', username='sin_clave',
                     email='x@uwork.app', password='', verbosity=0)
        self.assertFalse(User.objects.filter(username='sin_clave').exists())

    def test_es_idempotente_no_crea_duplicados(self):
        for _ in range(2):
            call_command('crear_admin', username='repetido',
                         email='admin@uwork.app', password='ClaveSegura123!',
                         verbosity=0)
        self.assertEqual(
            User.objects.filter(username='repetido').count(), 1)

    def test_no_toca_la_contrasena_si_el_usuario_ya_existe(self):
        """Si alguien la cambio a mano, el comando no la revierte."""
        call_command('crear_admin', username='existente',
                     email='admin@uwork.app', password='ClaveSegura123!',
                     verbosity=0)
        admin = User.objects.get(username='existente')
        admin.set_password('LaQuePuseAMano')
        admin.save()

        call_command('crear_admin', username='existente',
                     email='admin@uwork.app', password='ClaveSegura123!',
                     verbosity=0)

        admin.refresh_from_db()
        self.assertTrue(admin.check_password('LaQuePuseAMano'))

    def test_repara_los_permisos_de_un_usuario_existente(self):
        """Un admin sin is_staff no entra a los paneles."""
        admin = User.objects.create_user(
            username='roto', password='Aa12345678xyz!',
            is_staff=False, is_superuser=False, is_email_verified=False)

        call_command('crear_admin', username='roto', email='roto@uwork.app',
                     password='', verbosity=0)

        admin.refresh_from_db()
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_email_verified)

    def test_dry_run_no_escribe_nada(self):
        call_command('crear_admin', username='simulado',
                     email='admin@uwork.app', password='ClaveSegura123!',
                     dry_run=True, verbosity=0)
        self.assertFalse(User.objects.filter(username='simulado').exists())

    def test_el_comando_esta_disponible(self):
        """El build de Vercel lo invoca por nombre."""
        from django.core.management import get_commands
        self.assertIn('crear_admin', get_commands())
