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
if [ $? -ne 0 ]; then
    echo "❌ ERROR: Nginx configuration test failed"
    exit 1
fi

# Start nginx in the background
echo "Starting nginx..."
nginx -g "daemon off;" &
NGINX_PID=$!

# Wait for nginx to start
sleep 3

# Check if nginx is still running (alternative to pgrep)
if ! kill -0 $NGINX_PID 2>/dev/null; then
    echo "❌ ERROR: Nginx failed to start"
    exit 1
fi

# Double check by testing if nginx responds
if ! curl -f -s http://localhost:80/ >/dev/null 2>&1; then
    echo "⚠️ WARNING: Nginx started but not responding yet (will try later)"
else
    echo "✅ Nginx started and responding"
fi

echo "Starting Flask application with gunicorn..."

# Start the Flask application with gunicorn
exec /opt/venv/bin/gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile /dev/stdout \
    --error-logfile /dev/stderr \
    --preload \
    run:app
