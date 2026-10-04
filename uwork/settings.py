"""
Django settings for uwork project.
"""

import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Security
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-(6*)a_*7dvobfv6)r2fh@cz@n5k3+n0q-90z3*$c3!687dd0(+')

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

_hosts = os.environ.get('ALLOWED_HOSTS', '')
ALLOWED_HOSTS = _hosts.split(',') if _hosts else ['localhost', '127.0.0.1', '.vercel.app', '.neon.tech']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'jobs',
    'reviews',
    'notifications',
    'support',
    'legal',
    'moderation',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # §6.5.3 — cierre de sesión forzada para usuarios baneados
    'accounts.middleware.BannedUserMiddleware',
    # §6.5.3 — rate-limiting en endpoints sensibles
    'accounts.middleware.RateLimitMiddleware',
]

ROOT_URLCONF = 'uwork.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'notifications.context_processors.notif_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'uwork.wsgi.application'


# Database
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        ssl_require=not DEBUG,
    )
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'es'

TIME_ZONE = 'America/Bogota'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# R10 — Whitelist de correos institucionales (solo estudiantes).
# Para habilitar otra IES, agrega su dominio aquí; no requiere tocar código.
INSTITUTIONAL_DOMAINS = [
    d.strip().lower() for d in os.environ.get(
        'INSTITUTIONAL_DOMAINS', 'campusuninunez.edu.co'
    ).split(',') if d.strip()
]

# R11 — Verificación de email.
# Sin RESEND_API_KEY el correo de verificación se imprime en la consola
# (útil en desarrollo). Con la key, se envía el email real vía Resend.
SITE_URL = os.environ.get('SITE_URL', 'http://localhost:8000')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'no-reply@uwork.app')
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')

# Auth redirects
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'jobs:job_list'
LOGOUT_REDIRECT_URL = 'accounts:role_select'

# R11 — el backend exige correo verificado para poder iniciar sesión.
AUTHENTICATION_BACKENDS = ['accounts.backends.EmailVerifiedBackend']

# ── §6.5.3 — Headers de seguridad ───────────────────────────────
SECURE_CONTENT_TYPE_NOSNIFF = True          # X-Content-Type-Options
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
X_FRAME_OPTIONS = 'DENY'

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000           # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Content-Security-Policy.
# 'unsafe-inline' en style-src es necesario porque las plantillas del proyecto
# usan bloques <style> y atributos style=; en script-src no se permite, por lo
# que no puede ejecutarse JavaScript inyectado como etiqueta <script>.
CSP_DEFAULT_SRC = ["'self'"]
CSP_SCRIPT_SRC = ["'self'", 'https://cdn.jsdelivr.net']
CSP_STYLE_SRC = ["'self'", "'unsafe-inline'", 'https://cdn.jsdelivr.net',
                 'https://fonts.googleapis.com']
CSP_FONT_SRC = ["'self'", 'https://cdn.jsdelivr.net',
                'https://fonts.gstatic.com', 'data:']
CSP_IMG_SRC = ["'self'", 'data:', 'blob:']
CSP_CONNECT_SRC = ["'self'"]
CSP_FRAME_ANCESTORS = ["'none'"]
CSP_OBJECT_SRC = ["'none'"]
CSP_BASE_URI = ["'self'"]
CSP_FORM_ACTION = ["'self'"]

# ── §6.5.4 — SLA de respuesta a reportes de contenido ───────────
# El documento pide "definir tiempo máximo de respuesta (e.g. 24-48h)".
MODERATION_SLA_HOURS = int(os.environ.get('MODERATION_SLA_HOURS', '48'))

# ── §6.5.3 — Rate-limiting en endpoints sensibles ───────────────
# Ventana y máximo por prefijo de ruta. Los límites son por IP.
RATE_LIMITS = {
    '/login/': {'limit': 8, 'window': 300},
    '/register/': {'limit': 5, 'window': 3600},
    '/jobs/new/': {'limit': 10, 'window': 3600},
    '/jobs/job/': {'limit': 60, 'window': 300},
    '/verificar/reenviar/': {'limit': 5, 'window': 3600},
    '/soporte/': {'limit': 10, 'window': 3600},
}
RATE_LIMIT_ENABLED = True

# ── §6.5.3 — Validación de archivos subidos ─────────────────────
UPLOAD_MAX_SIZE_MB = 5
UPLOAD_ALLOWED_MIME = [
    'image/jpeg', 'image/png', 'image/webp',
]
UPLOAD_ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']

# ── §6.5.3 — Almacenamiento de archivos ─────────────────────────
# En Vercel el disco local no persiste. Si se define STORAGE_BACKEND se usa
# django-storages (requiere instalarlo y configurar las credenciales).
STORAGE_BACKEND = os.environ.get('STORAGE_BACKEND', '')
if STORAGE_BACKEND:
    DEFAULT_FILE_STORAGE = STORAGE_BACKEND
else:
    STORAGE_MIGRATION_PENDING = True
