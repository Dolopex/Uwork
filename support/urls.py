from django.urls import path
from . import views

app_name = 'support'

urlpatterns = [
    path('', views.ticket_create, name='create'),
    path('mis-reportes/', views.my_tickets, name='my_tickets'),
]
