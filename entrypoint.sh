#!/bin/bash
set -e

echo "Applying database migrations..."
python manage.py migrate

if [ "$1" = "worker" ]; then
    echo "Starting worker..."
    exec /bin/bash /app/scripts/background_refresh.sh
else
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
    echo "Starting Gunicorn..."
    exec gunicorn feverish.wsgi:application --bind 0.0.0.0:8000
fi
