#!/bin/bash

# Guest Management App - Portainer Deployment Script
# This script helps prepare the application for deployment in Portainer

echo "=== Guest Management App - Portainer Setup ==="
echo

# Check if we're in the right directory
if [ ! -f "Dockerfile" ] || [ ! -d "data" ]; then
    echo "❌ Error: Please run this script from the GuestManagement directory"
    echo "   Expected files: Dockerfile, data/ directory"
    exit 1
fi

echo "✅ Directory structure looks good"

# Generate a random secret key if not already set
if grep -q "your-random-secret-key-change-this" .env; then
    echo "🔑 Generating new SECRET_KEY..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    sed -i.bak "s/your-random-secret-key-change-this/$SECRET_KEY/" .env
    echo "✅ New SECRET_KEY generated and saved to .env"
else
    echo "✅ SECRET_KEY already customized"
fi

# Check if Docker is available
if command -v docker &> /dev/null; then
    echo "✅ Docker is available"
    
    # Offer to build the image locally for testing
    read -p "🐳 Would you like to build the Docker image locally for testing? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🔨 Building Docker image..."
        docker build -t guest-management:latest .
        if [ $? -eq 0 ]; then
            echo "✅ Docker image built successfully!"
            echo "   You can test it locally with:"
            echo "   docker run -p 8080:80 --env-file .env guest-management:latest"
        else
            echo "❌ Docker build failed. Please check the errors above."
        fi
    fi
else
    echo "⚠️  Docker not found. Make sure Docker is installed on your Portainer host."
fi

echo
echo "=== Deployment Instructions ==="
echo
echo "📋 To deploy in Portainer:"
echo
echo "Option 1 - Using Stacks (Recommended):"
echo "  1. Upload this entire directory to a Git repository"
echo "  2. In Portainer: Stacks → Add Stack → Repository"
echo "  3. Repository URL: [your-git-repo-url]"
echo "  4. Compose file path: docker-compose.yml"
echo "  5. Review environment variables and deploy"
echo
echo "Option 2 - Using Upload:"
echo "  1. Zip this entire directory"
echo "  2. In Portainer: Stacks → Add Stack → Upload"
echo "  3. Upload your zip file"
echo "  4. Review settings and deploy"
echo
echo "🌐 After deployment, access your app at:"
echo "   http://[your-server-ip]:8080"
echo
echo "📊 Monitor logs in Portainer:"
echo "   Containers → guest-management → Logs"
echo
echo "🔧 Configuration:"
echo "   - Edit .env file for environment variables"
echo "   - Modify docker-compose.yml for port changes"
echo "   - Database will be created automatically"
echo
echo "=== Important Notes ==="
echo "⚠️  Make sure to:"
echo "   - Change the SECRET_KEY in .env (done automatically above)"
echo "   - Adjust the port mapping if 8080 is already in use"
echo "   - Set up proper backups for the guest_data volume"
echo "   - Consider using a reverse proxy with SSL for production"
echo
echo "✅ Setup complete! Your application is ready for Portainer deployment."
