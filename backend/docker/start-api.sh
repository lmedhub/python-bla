#!/bin/sh
# Compose starts the API only once Postgres is healthy (depends_on), so there is no wait loop.
set -e

python manage.py migrate --noinput
# exec: gunicorn becomes PID 1 and receives Docker's stop signal directly.
# --no-control-socket: Docker manages the process, so gunicorn's runtime control socket
# (written under $HOME, which the app user does not have) is not needed.
exec gunicorn config.wsgi --bind 0.0.0.0:8000 --workers 2 --access-logfile - --no-control-socket
