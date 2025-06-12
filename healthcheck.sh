#!/bin/bash
# Health check script for the Flask application

# Check if nginx is responding
if ! curl -f -s http://localhost:80/ > /dev/null 2>&1; then
    echo "Application is not responding to HTTP requests"
    exit 1
fi

echo "All services are healthy"
exit 0
