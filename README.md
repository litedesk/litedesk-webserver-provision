

# Installation dependencies:

## Ubuntu

 - python-dev
 - libldap2-dev
 - libsasl2-dev


# How to get the code running on your local machine

 0. Clone this repo. This will be $PROJECT_ROOT.
 1. Create virtualenv: I usually just use "`virtualenv .`" in the
 $PROJECT_ROOT folder. The folders created by the virtualenv are already on
 .gitignore, so there is no problem.
 2. `pip install -r requirements.txt`

 3. Create your local_settings.py file. There is a
 local_settings.py.sample there with what you should need. In case you
 need to run/test the front-end code as well, and the path to the 'ui'
 folder of the frontend code to STATICFILES_DIRS.

 4. Still on $PROJECT_ROOT: `./src/manage.py syncdb` to make db
 migrations and install admin user.


# How to load initial users/fixtures

 0. Get the server running with `./src/manage.py runserver`
 1. Log-in as admin (http://localhost:8000/admin)
 2. Create user entry on "auth.user". This is from "Authentication"
 section, not from the "Tenant" one.
 3. From the tenant section, create a "Active Directory" with the our
 server credentials, and a "tenant" to represent a company that uuses
 it.
 4. Back in the command line, run "./src/manage.py load_users"
 