from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .auth_views import EmailVerificationAwareLoginView

app_name = 'accounts'

urlpatterns = [
    path('', views.role_select, name='role_select'),
    path('register/student/', views.register_student, name='register_student'),
    path('register/employer/', views.register_employer, name='register_employer'),
    path('login/', EmailVerificationAwareLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('balance/', views.balance, name='balance'),
    path('user/<int:pk>/', views.user_detail, name='user_detail'),

    # R11 — Verificación de email
    path('verificar/revisar-correo/', views.check_email, name='check_email'),
    path('verificar/email/<uuid:token>/', views.verify_email, name='verify_email'),
    path('verificar/reenviar/', views.resend_verification, name='resend_verification'),
    path('verificar/reenviar/mi-cuenta/', views.reenviar_mi_verificacion,
         name='resend_verification_mine'),

    # R16 — Eliminar mi cuenta (Ley 1581 de 2012, art. 17)
    path('eliminar-cuenta/', views.delete_account, name='delete_account'),
]
