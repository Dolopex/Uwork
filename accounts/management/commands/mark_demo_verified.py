"""Prepara los usuarios existentes para poder iniciar sesión.

Contexto: R11 exige verificar el correo antes de iniciar sesión, y R10
exige dominio institucional en el registro de estudiantes. Las bases de
datos sembradas antes de esos cambios quedaron con los usuarios sin
verificar y con correos @demo.com, así que nadie puede entrar.

Este comando corrige ambos casos sobre los usuarios que YA existen, sin
tocar sus contraseñas ni sus datos. Es idempotente: se puede repetir.

    python manage.py mark_demo_verified
    python manage.py mark_demo_verified --admin-password miClaveSegura
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = ('Marca los usuarios existentes como verificados y corrige el '
            'dominio de los correos de estudiantes (R10 y R11)')

    def add_arguments(self, parser):
        parser.add_argument(
            '--admin-password',
            help='Si se indica, redefine la contraseña del superusuario "admin".')
        parser.add_argument(
            '--only-unverified', action='store_true',
            help='No toca a los usuarios que ya están verificados.')
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Muestra qué cambiaría sin escribir nada.')

    @transaction.atomic
    def handle(self, *args, **options):
        solo_sin_verificar = options['only_unverified']
        simulacion = options['dry_run']

        consulta = User.objects.all()
        if solo_sin_verificar:
            consulta = consulta.filter(is_email_verified=False)

        verificados = 0
        correos = 0

        for usuario in consulta:
            cambios = []

            if not usuario.is_email_verified:
                cambios.append('is_email_verified=True')
                usuario.is_email_verified = True
                verificados += 1

            # R10: el estudiante debe usar correo institucional. Si tiene el
            # dominio de demo, se lo cambiamos al institucional configurado.
            if usuario.es_estudiante and usuario.email.endswith('@demo.com'):
                local = usuario.email.split('@', 1)[0]
                nuevo = '{}@{}'.format(local, self._dominio_institucional())
                cambios.append(
                    'email: {} -> {}'.format(usuario.email, nuevo))
                usuario.email = nuevo
                correos += 1

            if not cambios:
                continue

            if simulacion:
                self.stdout.write('  [dry-run] {}: {}'.format(
                    usuario.username, '; '.join(cambios)))
            else:
                usuario.save(update_fields=['is_email_verified', 'email'])
                self.stdout.write('  {}: {}'.format(
                    usuario.username, '; '.join(cambios)))

        if not simulacion:
            self._ajustar_admin(options.get('admin_password'), simulacion)

        self.stdout.write(self.style.SUCCESS(
            '\nListo. {} usuario(s) verificado(s), {} correo(s) institucional(es).'
            .format(verificados, correos)))
        if simulacion:
            self.stdout.write('No se escribió nada (--dry-run).')

    def _dominio_institucional(self):
        from django.conf import settings

        dominios = getattr(settings, 'INSTITUTIONAL_DOMAINS', [])
        return dominios[0] if dominios else 'campusuninunez.edu.co'

    def _ajustar_admin(self, contrasena, simulacion):
        """El superusuario también necesita estar verificado para entrar."""
        admin = User.objects.filter(username='admin').first()
        if admin is None:
            self.stdout.write(self.style.WARNING(
                'No existe un superusuario "admin".'))
            return

        campos = []
        if not admin.is_email_verified:
            admin.is_email_verified = True
            campos.append('is_email_verified')
        if not admin.is_staff:
            admin.is_staff = True
            campos.append('is_staff')
        if contrasena:
            admin.set_password(contrasena)
            campos.append('password')
            self.stdout.write('  admin: contraseña redefinida')

        if campos and not simulacion:
            admin.save(update_fields=campos)
        elif campos:
            self.stdout.write('  [dry-run] admin: {}'.format(', '.join(campos)))
        else:
            self.stdout.write('  admin: ya estaba listo')
