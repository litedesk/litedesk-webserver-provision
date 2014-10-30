import os
import sys
import site

# Add the site-packages of the chosen virtualenv to work with
site.addsitedir('/var/www/cross7.litedesk.de/litedesk-webserver-provision/venv/lib/python2.7/site-packages')

# Add the app's directory to the PYTHONPATH
sys.path.append('/var/www/cross7.litedesk.de/litedesk-webserver-provision/src')
sys.path.append('/var/www/cross7.litedesk.de/litedesk-webserver-provision/src/litedesk_service_api')

os.environ['DJANGO_SETTINGS_MODULE'] = 'litedesk_service_api.settings'

# Activate your virtual env
activate_env=os.path.expanduser("/var/www/cross7.litedesk.de/litedesk-webserver-provision/venv/bin/activate_this.py")
execfile(activate_env, dict(__file__=activate_env))

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()