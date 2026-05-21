#!/bin/bash
set -e

echo "Starting Esteem CBT Application..."

# Run database migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create superuser if environment variables are set (optional)
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Creating superuser..."
    python manage.py createsuperuser --noinput --username "$DJANGO_SUPERUSER_USERNAME" --email "$DJANGO_SUPERUSER_EMAIL" 2>/dev/null || true
fi

# Start Gunicorn
echo "Starting Gunicorn server..."
exec gunicorn school.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120