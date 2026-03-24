from django.contrib import admin
from .models import Job, Application


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'creador', 'estado', 'pago', 'categoria', 'fecha_limite']
    list_filter = ['estado', 'categoria']
    search_fields = ['titulo', 'descripcion']


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'trabajo', 'estado', 'created_at']
    list_filter = ['estado']
