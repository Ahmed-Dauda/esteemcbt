#!/bin/sh
# entrypoint.sh
set -e

# Run database migrations
python manage.py migrate --noinput

# Collect static files (using WhiteNoise)
python manage.py collectstatic --noinput --clear

# Start Gunicorn (or your WSGI server)
exec gunicorn school.wsgi:application --bind 0.0.0.0:8000 --workers 3