#!/bin/bash -ex
#export DJANGO_SETTINGS_MODULE=cloudbook_host_server.settings.testing
#lexport PYTHONPATH=$WORKSPACE/venv/lib/python2.7
stop_server(){
  pkill -f "manage.py runserver" || return 0
}

stop_server
echo "after stopserver"
find src -name *.pyc | xargs rm
virtualenv "$WORKSPACE/env"
source "$WORKSPACE/env/bin/activate"

if [ "$1" = "-profile" ]; then
    PY_PROFILE="-m cProfile -o cprof.out"
fi

mkdir -p "$WORKSPACE/logs"

pip install --download-cache=/tmp -r $WORKSPACE/requirements.txt || exit 23
# download the fixtures
rm -rf "$WORKSPACE/cross7-data" 2>/dev/null
git clone git@bitbucket.org:litedesk/cross7-data.git
rm -f "$WORKSPACE/app.db" 2>/dev/null
cp "$WORKSPACE/src/litedesk_service_api/local_settings.py.sample" "$WORKSPACE/src/litedesk_service_api/local_settings.py" 
cat <<EOT >> "$WORKSPACE/src/litedesk_service_api/local_settings.py"
import os
# TODO BASE_DIR is also defined in the settings.py
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if os.environ.get('JENKINS_HOME'):
    _FRONT_END_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..','..', '_cross7','workspace', 'ui'))
else:
    _FRONT_END_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..', 'cross7-front', 'ui'))

STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..', 'static'))



STATICFILES_DIRS = [
    _FRONT_END_ROOT,
    os.path.abspath(os.path.join(BASE_DIR, 'venv', 'lib', 'python2.7', 'site-packages', 'rest_framework', 'static'))
]


EXTRA_STATIC_ROOTS = (
    ('fonts', os.path.join(_FRONT_END_ROOT, 'fonts')),
    ('img', os.path.join(_FRONT_END_ROOT, 'img')),
)

MEDIA_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..', 'media'))
MEDIA_URL = '/media/'

SITE = {
    'host_url': 'http://localhost:8000',
    'name': 'Crosseven'
}


EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'litedesk.opensource@gmail.com'
EMAIL_HOST_PASSWORD = 't0ps3cr3t'

EOT





python "$WORKSPACE/src/manage.py" migrate || exit 23
python "$WORKSPACE/src/manage.py" loaddata "$WORKSPACE/cross7-data/fixtures/app_bootstrap.json"  || exit 23
echo "after loaddata"
python "$WORKSPACE/src/manage.py" load_users || exit 23
echo "after load_users"

/usr/local/sbin/daemonize -E BUILD_ID=dontKillMe "$WORKSPACE/env/bin/python" "$WORKSPACE/src/manage.py" runserver
echo "started server"
#python $PY_PROFILE "$WORKSPACE/src/manage.py" taskname || exit 23
