from .base import *

DEBUG = False

ALLOWED_HOSTS = ['*']


# One level above app directory
key_path = os.path.join(os.path.dirname(BASE_DIR), '.mfctracker-django-secret')
SECRET_KEY = open(key_path).read().strip()

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'mfctracker',
    }
}
