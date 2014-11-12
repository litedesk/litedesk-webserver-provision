#!/bin/bash -ex
#export DJANGO_SETTINGS_MODULE=cloudbook_host_server.settings.testing
#lexport PYTHONPATH=$WORKSPACE/venv/lib/python2.7
stop_server(){
  pkill -f "manage.py runserver" || return 0
}
virtualenv "$WORKSPACE/env"
source "$WORKSPACE/env/bin/activate"

if [ "$1" = "-profile" ]; then
    PY_PROFILE="-m cProfile -o cprof.out"
fi

mkdir -p "$WORKSPACE/logs"

pip install -r $WORKSPACE/requirements.txt -I || exit 23
# download the fixtures
rm -rf "$WORKSPACE/cross7-data" 2>/dev/null
git clone git@bitbucket.org:litedesk/cross7-data.git
rm -f "$WORKSPACE/app.db" 2>/dev/null
cp "$WORKSPACE/src/litedesk_service_api/local_settings.py.sample" "$WORKSPACE/src/litedesk_service_api/local_settings.py" 
python "$WORKSPACE/src/manage.py" migrate || exit 23
python "$WORKSPACE/src/manage.py" loaddata "$WORKSPACE/cross7-data/fixtures/app_bootstrap.json"  || exit 23
python "$WORKSPACE/src/manage.py" load_users || exit 23
stop_server
python "$WORKSPACE/src/manage.py" runserver || exit 23

#python $PY_PROFILE "$WORKSPACE/src/manage.py" taskname || exit 23