from .base import *

DEBUG = False

ALLOWED_HOSTS = ['*']

SECRET_KEY = open(os.path.expanduser('~/.mfctracker-django-secret')).read().strip()

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'mfctracker',
    }
}
