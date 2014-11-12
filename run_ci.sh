#!/bin/bash -ex
#export DJANGO_SETTINGS_MODULE=cloudbook_host_server.settings.testing
#export PYTHONPATH=$WORKSPACE/venv/lib/python2.7

virtualenv "$WORKSPACE/venv"
source "$WORKSPACE/venv/bin/activate"

if [ "$1" = "-profile" ]; then
    PY_PROFILE="-m cProfile -o cprof.out"
fi

mkdir -p "$WORKSPACE/logs"

# easy_install -U distribute || exit 23
pip install --download-cache=/tmp -r $WORKSPACE/requirements.txt || exit 23
# download the fixtures
git clone git@bitbucket.org:litedesk/cross7-data.git
rm "$WORKSPACE/app.db"
python "$WORKSPACE/src/manage.py" migrate || exit 23
python "$WORKSPACE/src/manage.py" loaddata "$WORKSPACE/cross7-data/fixtures/app_bootstrap.json"  || exit 23
python "$WORKSPACE/src/manage.py" load_users || exit 23
pkill -f "manage.py runserver"
python "$WORKSPACE/src/manage.py" runserver || exit 23



#python "$WORKSPACE/src/manage.py" reset_db --noinput --router=default || exit 23
#python "$WORKSPACE/src/manage.py" syncdb --noinput || exit 23
#python "$WORKSPACE/src/manage.py" migrate || exit 23
#python $PY_PROFILE "$WORKSPACE/src/manage.py" jenkins core ccp password_reset manage_endusers update_interface || exit 23

