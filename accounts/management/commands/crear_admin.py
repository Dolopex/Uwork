"""Crea (o repara) el superusuario de la plataforma.

Por que no `createsuperuser` de Django:

- No es idempotente. Si el usuario ya existe, falla y el despliegue se cae.
- No pone `is_email_verified=True`. El backend de autenticacion
  (accounts.backends.EmailVerifiedBackend) rechaza las cuentas sin
  verificar, asi que un superusuario creado con createsuperuser se queda
  sin poder iniciar sesion.
- Es interactivo: pide la contrasena por terminal, y en un despliegue de
  Vercel no hay terminal.

Este comando resuelve las tres cosas: se puede correr en cada despliegue
sin riesgo, deja al superusuario en condiciones de entrar, y lee la
contrasena del entorno para no tener que escribirla en un argumento que
quede en el historial de la shell.

    python manage.py crear_admin
    python manage.py crear_admin --username root --email root@uwork.app
    python manage.py crear_admin --dry-run

La contrasena sale de DJANGO_SUPERUSER_PASSWORD. Si no esta definida y
tampoco se pasa por --password, el comando no hace nada y lo dice: es
preferible no crear el superusuario a crearlo con una contrasena
predecible.
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import capfirst

User = get_user_model()


class Command(BaseCommand):
    help = ('Crea el superusuario de la plataforma, o repara el que ya '
            'existe. Lee la contrasena de DJANGO_SUPERUSER_PASSWORD.')

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            default=os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin'),
            help='Nombre de usuario del superusuario.')
        parser.add_argument(
            '--email',
            default=os.environ.get('DJANGO_SUPERUSER_EMAIL', ''),
            help='Correo electronico del superusuario.')
        parser.add_argument(
            '--password',
            default=os.environ.get('DJANGO_SUPERUSER_PASSWORD', ''),
            help=('Contrasena. Si se omite, se toma de '
                  'DJANGO_SUPERUSER_PASSWORD.'))
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Muestra que haria sin escribir nada.')

    @transaction.atomic
    def handle(self, *args, **options):
        username = (options['username'] or 'admin').strip()
        email = (options['email'] or '').strip()
        contrasena = options['password'] or ''
        simulacion = options['dry_run']

        if not username:
            raise CommandError('Falta el nombre de usuario del superusuario.')

        existente = User.objects.filter(username=username).first()

        if existente is not None:
            self._reparar(existente, contrasena, simulacion)
            return

        if not contrasena:
            # Sin contrasena no se crea nada. Un superusuario con una
            # contrasena predecible es peor que no tener superusuario.
            self.stdout.write(self.style.WARNING(
                'El superusuario "{}" no existe y no hay contrasena '
                'definida. Define DJANGO_SUPERUSER_PASSWORD y vuelve a '
                'correr el comando.'.format(username)))
            return

        if not email:
            self.stdout.write(self.style.WARNING(
                'No hay correo definido para el superusuario. Se creara '
                'sin correo, que es valido pero no permite recuperarlo.'))

        if simulacion:
            self.stdout.write('[dry-run] Se crearia el superusuario "{}" '
                              'con correo "{}".'.format(username, email or '(sin correo)'))
            return

        usuario = User.objects.create_superuser(
            username=username, email=email, password=contrasena)
        # R11: sin verificar, el backend no lo deja entrar.
        usuario.is_email_verified = True
        usuario.is_staff = True
        usuario.is_superuser = True
        usuario.save(update_fields=[
            'is_email_verified', 'is_staff', 'is_superuser'])
        self.stdout.write(self.style.SUCCESS(
            'Superusuario "{}" creado (correo verificado, acceso al panel).'
            .format(usuario.username)))

    def _reparar(self, usuario, contrasena, simulacion):
        """El superusuario ya existe: se asegurar sus permisos.

        La contrasena NO se toca: si alguien la cambio a mano, este
        comando no debe devolvarla a la que el tiene delante.
        """
        cambios = []
        if not usuario.is_staff:
            usuario.is_staff = True
            cambios.append('is_staff')
        if not usuario.is_superuser:
            usuario.is_superuser = True
            cambios.append('is_superuser')
        # R11: el superusuario tambien necesita correo verificado.
        if not usuario.is_email_verified:
            usuario.is_email_verified = True
            cambios.append('is_email_verified')
        if not usuario.is_active:
            usuario.is_active = True
            cambios.append('is_active')

        if simulacion:
            if cambios:
                self.stdout.write('[dry-run] "{}": {}'.format(
                    usuario.username, ', '.join(cambios)))
            else:
                self.stdout.write('[dry-run] "{}": ya estaba listo.'.format(
                    usuario.username))
            return

        if cambios:
            usuario.save(update_fields=cambios)
            self.stdout.write(self.style.SUCCESS(
                '"{}" reparado: {}.'.format(
                    usuario.username, ', '.join(cambios))))
        else:
            self.stdout.write('"{}" ya estaba listo.'.format(usuario.username))

        if contrasena:
            self.stdout.write(self.style.WARNING(
                'El superusuario ya existia: su contrasena no se ha '
                'modificado. Si quieres redefinirla, hazlo a mano desde el '
                'panel de administracion.'))
