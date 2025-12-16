#!/bin/bash
set -e

echo "Applying database migrations..."
python manage.py migrate

echo "Starting Gunicorn..."
exec gunicorn feverish.wsgi:application --bind 0.0.0.0:8000
