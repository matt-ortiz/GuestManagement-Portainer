# Guest Management Flask App

A Flask-based guest management system designed for easy deployment with Docker and Portainer.

## Quick Deploy to Portainer

### Method 1: Direct Repository Deploy (Recommended)

1. **In Portainer**:
   - Go to "Stacks" → "Add Stack"
   - Choose "Repository"
   - Repository URL: `https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git`
   - Repository reference: `refs/heads/main` (or `master`)
   - Compose file path: `docker-compose.yml`
   - Stack name: `guest-management`

2. **Environment Variables** (Optional - can be set in Portainer):
   - `SECRET_KEY`: Your secure secret key
   - `PORT`: Change from default 8080 if needed

3. **Deploy** and access at `http://your-server:8080`

### Method 2: Clone and Build Locally

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
docker-compose up -d
```

## Configuration

### Environment Variables

Edit the `.env` file or set in Portainer:

```env
SECRET_KEY=your-secure-random-key-here
DATABASE_URL=sqlite:////app/instance/guests.db
FLASK_ENV=production
FLASK_DEBUG=0
```

### Port Configuration

Default port is 8080. To change:
- Edit `docker-compose.yml`
- Change `"8080:80"` to `"YOUR_PORT:80"`

## Features

- 🐳 **Docker-ready**: Optimized containerization
- 🔄 **Auto-updates**: Easy updates via git pull
- 📊 **Health monitoring**: Built-in health checks
- 💾 **Data persistence**: Automatic volume management
- 🚀 **Production-ready**: Nginx reverse proxy included
- 📝 **Logging**: Comprehensive application logging

## File Structure

```
├── docker-compose.yml      # Portainer deployment config
├── Dockerfile             # Container build instructions
├── nginx.conf             # Reverse proxy configuration
├── data/                  # Flask application
│   ├── app/              # Application code
│   ├── config.py         # App configuration
│   ├── run.py            # Application entry point
│   └── requirements.txt  # Python dependencies
└── docs/                 # Documentation
```

## Volumes

- `guest_data`: Database and instance files (`/app/instance`)
- `guest_logs`: Application logs (`/app/logs`)

## Support

- **Health Check**: Built-in container health monitoring
- **Logs**: Available in Portainer container logs
- **Database**: SQLite with automatic initialization

## Security Notes

⚠️ **Important**: Change the `SECRET_KEY` in your `.env` file before production deployment!

## Updates

To update your deployment:
1. Push changes to your Git repository
2. In Portainer: Stacks → your-stack → Editor → "Update the stack"
3. Portainer will pull the latest code and rebuild

---

**Ready to deploy?** Just use the repository URL in Portainer and you're good to go! 🚀
