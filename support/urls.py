from django.urls import path

from . import views

app_name = 'support'

urlpatterns = [
    path('', views.ticket_create, name='create'),
    path('mis-reportes/', views.my_tickets, name='my_tickets'),
    # Panel de soporte para el personal
    path('panel/', views.panel_tickets, name='panel_tickets'),
    path('panel/<int:pk>/resolver/', views.resolver_ticket,
         name='resolver_ticket'),
]
