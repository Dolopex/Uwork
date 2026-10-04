from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'rol', 'is_email_verified', 'is_banned', 'calificacion_promedio', 'is_staff']
    list_filter = ['rol', 'is_staff', 'is_email_verified', 'is_banned']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Perfil U-Work', {'fields': ('rol', 'foto', 'cedula', 'telefono', 'direccion', 'fecha_nacimiento', 'habilidades', 'calificacion_promedio')}),
        ('Datos de Estudiante', {'fields': ('universidad', 'carrera', 'semestre', 'foto_carnet')}),
        ('Verificación de email (R11)', {'fields': ('is_email_verified', 'email_verification_token', 'email_verification_sent_at')}),
        ('Sanción (§6.5.4)', {'fields': ('is_banned', 'baneo_hasta', 'motivo_baneo')}),
        ('Seguridad', {'fields': ('pregunta_seguridad', 'respuesta_seguridad')}),
    )
