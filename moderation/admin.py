from django.contrib import admin

from .models import Apelacion, Reporte, Sancion


@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ['pk', 'trabajo', 'motivo', 'estado', 'sla_vencido',
                    'reportante', 'created_at']
    list_filter = ['estado', 'motivo', 'resolucion']
    search_fields = ['trabajo__titulo', 'reportante__username', 'descripcion']
    readonly_fields = ['created_at', 'resuelto_at', 'plazo_respuesta']


@admin.register(Sancion)
class SancionAdmin(admin.ModelAdmin):
    """Bitácora de auditoría. No se permite editar ni borrar.

    La trazabilidad exige que el registro de una sanción sea inmutable; para
    corregirla se agrega una nueva fila con el levantamiento.
    """
    list_display = ['pk', 'usuario', 'tipo', 'aplicada_por', 'created_at',
                    'hasta', 'levantada_at']
    list_filter = ['tipo', 'created_at']
    search_fields = ['usuario__username', 'motivo']
    readonly_fields = [f.name for f in Sancion._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Apelacion)
class ApelacionAdmin(admin.ModelAdmin):
    list_display = ['pk', 'usuario', 'sancion', 'estado', 'created_at',
                    'resuelta_at']
    list_filter = ['estado']
    search_fields = ['usuario__username', 'motivo', 'respuesta']
