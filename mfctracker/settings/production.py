from .base import *

DEBUG = False

SECRET_KEY = open(os.path.expanduser('~/.mfctracker-django-secret')).read().strip()

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
    }
}
