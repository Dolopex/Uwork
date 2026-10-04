from django.urls import path, reverse_lazy
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

    # R2 (vista faltante del módulo de autenticación) + §6.5.3
    # "Vistas de 'Olvidé mi contraseña' y cambio de contraseña"
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        email_template_name='accounts/password_reset_email.txt',
        subject_template_name='accounts/password_reset_subject.txt',
    ), name='password_reset'),
    # Las pantallas password_reset_done y password_reset_complete se
    # registran en uwork/urls.py: Django 5.2 las resuelve por nombre global.
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html'),
        name='password_reset_confirm'),
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change.html',
        success_url=reverse_lazy('accounts:password_change_done')),
        name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'),
        name='password_change_done'),

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
