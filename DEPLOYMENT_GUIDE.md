# 🚀 Guest Management App - Portainer Migration Summary

## ✅ Changes Made

### 1. **File Structure Reorganization**
- Moved all application code to `data/` directory
- Updated all file paths from UnRAID-specific paths to container paths
- Consolidated requirements files

### 2. **Docker Configuration**
- **New Dockerfile**: Optimized for Portainer deployment
- **Updated docker-compose.yml**: Removed UnRAID-specific network/volume configs
- **New nginx.conf**: Cleaned up and optimized for container environment
- **New entrypoint.sh**: Proper container startup sequence

### 3. **Application Updates**
- **config.py**: Updated database path to `/app/instance/guests.db`
- **.env**: Updated environment variables for container paths
- **requirements.txt**: Consolidated and cleaned up dependencies

### 4. **Production Features**
- **Health checks**: Automatic container health monitoring
- **Volume management**: Persistent data storage for database and logs
- **Security headers**: Basic security improvements in nginx
- **Log handling**: Proper logging configuration

## 📋 Deployment Steps

### Option 1: Upload to Portainer (Quickest)

1. **Zip the entire `GuestManagement` folder**
2. **In Portainer**: 
   - Go to "Stacks"
   - Click "Add stack"
   - Choose "Upload"
   - Upload your zip file
   - Name: `guest-management`
3. **Review settings**:
   - Port: Will be available on port 8080
   - Volumes: `guest_data` and `guest_logs` will be created
4. **Deploy the stack**

### Option 2: Git Repository (Recommended for updates)

1. **Create a Git repository** and push this code
2. **In Portainer**:
   - Go to "Stacks"
   - Click "Add stack" 
   - Choose "Repository"
   - Repository URL: Your git repo URL
   - Compose file path: `docker-compose.yml`
3. **Deploy**

### Option 3: Build Custom Image

1. **Build locally**:
   ```bash
   cd GuestManagement
   docker build -t guest-management:latest .
   ```
2. **Push to registry** (Docker Hub, etc.)
3. **Deploy from Portainer** using your image

## 🔧 Configuration

### Environment Variables (Important!)
Update these in your `.env` file or Portainer stack:

```env
SECRET_KEY=your-secure-random-key-here  # MUST CHANGE!
DATABASE_URL=sqlite:////app/instance/guests.db
FLASK_ENV=production
FLASK_DEBUG=0
```

### Port Configuration
- **Default**: Application runs on port 8080
- **To change**: Edit `docker-compose.yml`, line with `"8080:80"`
- **Example**: `"3000:80"` to use port 3000

## 📊 After Deployment

### Access Your App
- **URL**: `http://your-server-ip:8080`
- **First run**: Database will be created automatically
- **Logs**: Available in Portainer container logs

### Data Persistence
- **Database**: Stored in `guest_data` volume
- **Logs**: Stored in `guest_logs` volume
- **Backups**: Backup these volumes regularly

### Monitoring
- **Health checks**: Container will show healthy/unhealthy status
- **Logs**: Real-time logs in Portainer
- **Resources**: CPU/Memory usage in Portainer stats

## ⚠️ Important Security Notes

1. **Change SECRET_KEY**: The default key MUST be changed!
2. **Firewall**: Only expose port 8080 if needed externally
3. **Reverse Proxy**: Consider Traefik/nginx for SSL termination
4. **Backups**: Set up regular volume backups

## 🔍 Troubleshooting

### Common Issues:
- **Port conflicts**: Change port in docker-compose.yml
- **Permission issues**: Volumes are handled automatically
- **Database errors**: Check that guest_data volume is writable
- **Static files**: Should work automatically with nginx

### Checking Status:
1. **Container health**: Look for green/red status in Portainer
2. **Application logs**: Container logs in Portainer
3. **Web access**: Try accessing http://server-ip:8080

## 🎯 Key Differences from UnRAID

| UnRAID | Portainer |
|--------|-----------|
| `/mnt/user/appdata/GuestManagement` | `/app` (in container) |
| Host bind mounts | Docker volumes |
| Custom br0 network | Default bridge network |
| Manual container management | Stack-based deployment |

Your application is now ready for production deployment in Portainer! 🎉
