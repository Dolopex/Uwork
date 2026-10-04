"""
URL configuration for uwork project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.views import (
    PasswordResetCompleteView,
    PasswordResetDoneView,
)
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('sw.js', TemplateView.as_view(template_name='sw.js', content_type='application/javascript'), name='sw'),
    path('admin/', admin.site.urls),

    # Django 5.2 resuelve 'password_reset_done' y 'password_reset_complete'
    # por su nombre global (sin namespace), por eso se registran aqui y no
    # dentro de accounts.urls.
    path('password_reset/done/', PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html',
        extra_context={'view': 'password_reset'}),
        name='password_reset_done'),
    path('reset/done/', PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'),
        name='password_reset_complete'),

    path('', include('accounts.urls')),
    path('jobs/', include('jobs.urls')),
    path('reviews/', include('reviews.urls')),
    path('notificaciones/', include('notifications.urls')),
    path('soporte/', include('support.urls')),
    path('', include('legal.urls')),
    path('moderacion/', include('moderation.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
