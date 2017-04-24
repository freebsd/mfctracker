from .base import *

SECRET_KEY = 'o4c6#^(x44smd70-4=yghiguu25m^89bmtsufxqpn-!e(gqoy8'

DEBUG = True

INSTALLED_APPS += [ 'debug_toolbar' ]
MIDDLEWARE = [ 'debug_toolbar.middleware.DebugToolbarMiddleware' ] + MIDDLEWARE

def custom_show_toolbar(request):
    return True  # Always show toolbar

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': 'mfctracker.settings.development.custom_show_toolbar',
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
