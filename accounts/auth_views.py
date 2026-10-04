"""Vista de inicio de sesión con aviso de verificación pendiente — R11.

El backend accounts.backends.EmailVerifiedBackend rechaza el login de
cuentas sin correo verificado. Sin esta vista, AuthenticationForm mostraría
un error genérico de "credenciales inválidas" y el usuario no sabría que
lo que falta es confirmar el correo. Esta vista detecta ese caso concreto,
lo explica y ofrece reenviar el enlace sin salir de la pantalla.
"""
from django.contrib import messages
from django.contrib.auth import views as auth_views

from .models import User


class EmailVerificationAwareLoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'

    def form_valid(self, form):
        return super().form_valid(form)

    def form_invalid(self, form):
        # Si el usuario existe pero no ha verificado su correo, el fallo no
        # es de contraseña: lo decimos explícitamente y damos la opción de
        # reenviar el enlace.
        username = (form.data.get('username') or '').strip()
        pendiente = None
        if username:
            usuario = User.objects.filter(username__iexact=username).first()
            if usuario is not None and not usuario.is_email_verified:
                pendiente = usuario.email
                form.add_error(None, (
                    'Tu correo ({}) aún no está verificado. Revisa tu bandeja '
                    'de entrada o usa el enlace "Reenviar verificación" para '
                    'recibir uno nuevo.'.format(usuario.email)
                ))
        return self.render_to_response(
            self.get_context_data(form=form, pending_email=pendiente),
        )
