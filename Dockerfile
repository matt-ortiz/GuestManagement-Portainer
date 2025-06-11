# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nginx \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create application directories
RUN mkdir -p /app/instance /app/logs

# Copy requirements first for better layer caching
COPY data/requirements.txt .

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy application code
COPY data/ .

# Set proper permissions
RUN chown -R www-data:www-data /app && \
    chmod -R 755 /app

# Create entrypoint and health check scripts
COPY entrypoint.sh /entrypoint.sh
COPY healthcheck.sh /healthcheck.sh
RUN chmod +x /entrypoint.sh /healthcheck.sh

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD /healthcheck.sh || exit 1

# Expose port 80
EXPOSE 80

# Use entrypoint script
ENTRYPOINT ["/entrypoint.sh"]
