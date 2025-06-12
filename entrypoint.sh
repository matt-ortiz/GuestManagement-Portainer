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

# Test nginx config before starting
echo "Testing nginx configuration..."
nginx -t

# Start nginx in the background
echo "Starting nginx..."
nginx

# Wait for nginx to start and verify it's running
sleep 3
if ! pgrep nginx > /dev/null; then
    echo "❌ ERROR: Nginx failed to start"
    exit 1
fi
echo "✅ Nginx started successfully"

echo "Starting Flask application with gunicorn..."

# Start the Flask application with gunicorn
# Remove --user/--group for now to debug permission issues
exec /opt/venv/bin/gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile /dev/stdout \
    --error-logfile /dev/stderr \
    --preload \
    run:app
