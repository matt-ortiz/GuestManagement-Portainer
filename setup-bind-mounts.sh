#!/bin/bash

echo "🚀 Setting up Guest Management with Bind Mounts"
echo "==============================================="
echo

HOST_PATH="/etc/docker/config/guestmanagement"
APP_PATH="$HOST_PATH/app"

echo "📁 Creating host directories..."
sudo mkdir -p "$APP_PATH"

echo "📋 Setting up directory structure..."

# Create the main application structure
sudo mkdir -p "$APP_PATH/app"
sudo mkdir -p "$APP_PATH/app/static"
sudo mkdir -p "$APP_PATH/app/templates"
sudo mkdir -p "$APP_PATH/app/utils"
sudo mkdir -p "$APP_PATH/instance"
sudo mkdir -p "$APP_PATH/logs"

echo "✅ Directory structure created"

echo "🔧 Setting proper permissions..."
# Set ownership to www-data (user ID 33)
sudo chown -R 33:33 "$HOST_PATH"
sudo chmod -R 755 "$HOST_PATH"

# Make instance and logs writable
sudo chmod -R 777 "$APP_PATH/instance"
sudo chmod -R 777 "$APP_PATH/logs"

echo "✅ Permissions set"

echo "📂 Directory structure:"
echo "├── $APP_PATH/"
echo "│   ├── app/                    # Python Flask application"
echo "│   │   ├── static/            # CSS, JS, images"
echo "│   │   ├── templates/         # HTML templates"
echo "│   │   ├── utils/             # Helper functions"
echo "│   │   ├── __init__.py        # Flask app initialization"
echo "│   │   ├── routes.py          # URL routes"
echo "│   │   ├── models.py          # Database models"
echo "│   │   └── ...                # Other Python files"
echo "│   ├── instance/              # Database files"
echo "│   ├── logs/                  # Application logs"
echo "│   ├── config.py              # App configuration"
echo "│   ├── run.py                 # Application entry point"
echo "│   └── requirements.txt       # Python dependencies"

echo
echo "🎯 Next Steps:"
echo "1. Copy your application files to: $APP_PATH"
echo "2. Copy your database to: $APP_PATH/instance/guests.db"
echo "3. Push updated docker-compose.yml to Git"
echo "4. Update your Portainer stack"
echo
echo "💡 Benefits:"
echo "✅ Edit Python code directly: $APP_PATH/app/"
echo "✅ Access database directly: $APP_PATH/instance/guests.db"
echo "✅ View logs directly: $APP_PATH/logs/"
echo "✅ No Docker volume complexity!"
echo
echo "🔧 File editing:"
echo "   nano $APP_PATH/app/routes.py"
echo "   nano $APP_PATH/config.py"
echo "   sqlite3 $APP_PATH/instance/guests.db"
echo
echo "Setup complete! 🎉"
