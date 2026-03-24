from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'rol', 'calificacion_promedio', 'is_staff']
    list_filter = ['rol', 'is_staff']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Perfil U-Work', {'fields': ('rol', 'foto', 'cedula', 'telefono', 'direccion', 'fecha_nacimiento', 'habilidades', 'calificacion_promedio')}),
        ('Datos de Estudiante', {'fields': ('universidad', 'carrera', 'semestre', 'foto_carnet')}),
        ('Seguridad', {'fields': ('pregunta_seguridad', 'respuesta_seguridad')}),
    )
