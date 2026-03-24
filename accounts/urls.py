from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.role_select, name='role_select'),
    path('register/student/', views.register_student, name='register_student'),
    path('register/employer/', views.register_employer, name='register_employer'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('balance/', views.balance, name='balance'),
    path('user/<int:pk>/', views.user_detail, name='user_detail'),
]
