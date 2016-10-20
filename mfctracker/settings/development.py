from .base import *

SECRET_KEY = 'o4c6#^(x44smd70-4=yghiguu25m^89bmtsufxqpn-!e(gqoy8'

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'mfctracker_dev',
    }
}

INSTALLED_APPS += [ 'debug_toolbar' ]
MIDDLEWARE = [ 'debug_toolbar.middleware.DebugToolbarMiddleware' ] + MIDDLEWARE

def custom_show_toolbar(request):
    return True  # Always show toolbar

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': 'mfctracker.settings.custom_show_toolbar',
}
