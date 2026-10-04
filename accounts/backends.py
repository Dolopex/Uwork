"""Backend de autenticación con verificación de email — R11.

R11 — Verificación de email
Detalle:   El usuario debe hacer clic en el enlace de confirmación antes de
           activar la cuenta.

ModelBackend ya rechaza usuarios con is_active=False. Este backend añade la
condición de R11: un usuario cuyo correo no ha sido verificado no puede
iniciar sesión, aunque la contraseña sea correcta.
"""
from django.contrib.auth.backends import ModelBackend


class EmailVerifiedBackend(ModelBackend):
    """Permite autenticarse solo a cuentas con correo verificado."""

    def user_can_authenticate(self, user):
        return super().user_can_authenticate(user) and user.is_email_verified
