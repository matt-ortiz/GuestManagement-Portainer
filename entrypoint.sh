#!/bin/bash

echo "Starting Guest Management Application..."

# First-time setup: Copy application files if they don't exist
if [ ! -f "/app/run.py" ]; then
    echo "🚀 First run detected - setting up application files..."
    
    # Copy all application files from template
    cp -r /app-template/* /app/
    
    # Create necessary directories
    mkdir -p /app/instance /app/logs
    mkdir -p /app/app/static /app/app/templates /app/app/utils
    
    echo "✅ Application files copied to bind mount"
fi

# Always ensure proper permissions and directory structure
mkdir -p /app/instance /app/logs
chown -R www-data:www-data /app/instance /app/logs
chmod -R 755 /app/instance /app/logs

# Make instance and logs writable  
chmod 777 /app/instance /app/logs

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

# Wait for nginx to start and verify it's running
sleep 3
if ! kill -0 $NGINX_PID 2>/dev/null; then
    echo "❌ ERROR: Nginx failed to start"
    exit 1
fi

echo "✅ Nginx started successfully"
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
