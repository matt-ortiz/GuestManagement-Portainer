#!/bin/bash

# Start nginx in the background
nginx

# Start the Flask application with gunicorn
exec /opt/venv/bin/gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile /dev/stdout \
    --error-logfile /dev/stderr \
    --preload \
    run:app
