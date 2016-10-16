from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'o4c6#^(x44smd70-4=yghiguu25m^89bmtsufxqpn-!e(gqoy8'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
