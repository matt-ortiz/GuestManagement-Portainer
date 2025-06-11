#!/bin/bash

echo "Starting Guest Management Application..."

# Ensure proper permissions for data directories
chown -R www-data:www-data /app/instance /app/logs
chmod -R 755 /app/instance /app/logs

# Create database directory if it doesn't exist
mkdir -p /app/instance
chown www-data:www-data /app/instance
chmod 755 /app/instance

echo "Permissions set for data directories"

# Start nginx in the background
echo "Starting nginx..."
nginx

# Wait for nginx to start
sleep 2

echo "Starting Flask application with gunicorn..."

# Start the Flask application with gunicorn
exec /opt/venv/bin/gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile /dev/stdout \
    --error-logfile /dev/stderr \
    --preload \
    --user www-data \
    --group www-data \
    run:app
