#!/usr/bin/env python


import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'litedesk_service_api.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
