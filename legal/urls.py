from django.urls import path

from . import views

app_name = 'legal'

urlpatterns = [
    # R14 — Términos y Condiciones
    path('terminos-y-condiciones/', views.terminos, name='terminos'),
    # R15 — Política de Privacidad
    path('politica-de-privacidad/', views.privacidad, name='privacidad'),
]
