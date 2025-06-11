#!/bin/bash
# Health check script for the Flask application

# Check if nginx is running
if ! pgrep nginx > /dev/null; then
    echo "Nginx is not running"
    exit 1
fi

# Check if gunicorn is running
if ! pgrep gunicorn > /dev/null; then
    echo "Gunicorn is not running" 
    exit 1
fi

# Check if the application responds to HTTP requests
if ! curl -f http://localhost:80/ > /dev/null 2>&1; then
    echo "Application is not responding to HTTP requests"
    exit 1
fi

echo "All services are healthy"
exit 0
