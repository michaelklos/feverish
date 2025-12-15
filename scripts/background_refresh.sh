#!/bin/bash
echo "Starting background refresh worker..."
while true; do
    echo "Running refresh_feeds..."
    python manage.py refresh_feeds
    echo "Sleeping for 15 minutes..."
    sleep 900
done
