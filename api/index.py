import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'uwork.settings')

from uwork.wsgi import application as app
