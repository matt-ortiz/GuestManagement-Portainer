#!/bin/bash

echo "🚀 Setting up Guest Management App for Git Repository"
echo "=================================================="
echo

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ] || [ ! -d "data" ]; then
    echo "❌ Error: Please run this script from the GuestManagement directory"
    exit 1
fi

echo "✅ Directory structure verified"

# Clean up Mac-specific files
echo "🧹 Cleaning up system files..."
find . -name ".DS_Store" -delete 2>/dev/null || true
find . -name "._*" -delete 2>/dev/null || true

# Clean up Python cache
echo "🐍 Cleaning up Python cache files..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Remove log files (they'll be recreated)
echo "📝 Cleaning up log files..."
rm -f data/logs/*.log* 2>/dev/null || true

# Remove backup database files but keep the main one
echo "💾 Cleaning up backup database files..."
rm -f data/instance/*copy* 2>/dev/null || true
rm -f data/instance/*.bak 2>/dev/null || true

echo
echo "🔧 Git Repository Setup:"
echo "1. Initialize git repository:"
echo "   git init"
echo
echo "2. Add all files:"
echo "   git add ."
echo
echo "3. Create initial commit:"
echo "   git commit -m 'Initial commit: Guest Management Flask App for Portainer'"
echo
echo "4. Add your remote repository:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git"
echo
echo "5. Push to repository:"
echo "   git branch -M main"
echo "   git push -u origin main"
echo
echo "📋 Portainer Deployment Steps:"
echo "1. Go to Portainer → Stacks → Add Stack"
echo "2. Choose 'Repository'"
echo "3. Repository URL: https://github.com/YOUR_USERNAME/YOUR_REPO.git"
echo "4. Compose file path: docker-compose.yml"
echo "5. Stack name: guest-management"
echo "6. Set environment variables (especially SECRET_KEY!)"
echo "7. Deploy!"
echo
echo "⚠️  IMPORTANT SECURITY NOTES:"
echo "- Change SECRET_KEY before production deployment"
echo "- The .env file contains placeholder values only"
echo "- Set real values in Portainer environment variables"
echo
echo "✅ Repository is ready for Git! Follow the steps above to deploy."
