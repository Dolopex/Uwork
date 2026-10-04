from django.urls import path

from . import views

app_name = 'moderation'

urlpatterns = [
    # Reportes por usuarios
    path('reportar/<int:pk>/', views.reportar_trabajo, name='reportar_trabajo'),

    # Panel de moderación (staff)
    path('panel/', views.panel_reportes, name='panel_reportes'),
    path('panel/reporte/<int:pk>/resolver/', views.resolver_reporte,
         name='resolver_reporte'),

    # Bitácora de sanciones
    path('bitacora/', views.bitacora_sanciones, name='bitacora'),
    path('bitacora/<int:pk>/levantar/', views.levantar_sancion,
         name='levantar_sancion'),

    # Apelaciones
    path('apelaciones/', views.panel_apelaciones, name='apelaciones'),
    path('apelaciones/<int:pk>/resolver/', views.resolver_apelacion,
         name='resolver_apelacion'),
]
