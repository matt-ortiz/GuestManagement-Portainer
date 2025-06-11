# 🐳 Portainer Deployment Guide - Private Setup

Since you prefer not to use public Git hosting, here are the best ways to deploy privately in Portainer.

## 🎯 **Option 1: Portainer Stacks Upload (Recommended)**

### Step 1: Prepare the Files
1. **Zip the GuestManagement folder** (excluding .git if you have one)
2. **Clean up first** to reduce size:
   ```bash
   find . -name ".DS_Store" -delete
   find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
   rm -f data/logs/*.log* 2>/dev/null || true
   ```

### Step 2: Deploy in Portainer
1. **Go to Portainer** → Stacks → Add Stack
2. **Choose "Upload"** method
3. **Upload your zip file**
4. **Name**: `guest-management`
5. **Configure Environment Variables** (see below)
6. **Deploy**

## 🔧 **Environment Variables in Portainer**

**In the Portainer stack configuration, add these environment variables:**

### **Required Variables:**
- `SECRET_KEY` = `your-secure-random-key-here-123456789abcdef`
- `APP_PORT` = `8080` (or whatever port you want)

### **Optional Variables:**
- `FLASK_ENV` = `production`
- `FLASK_DEBUG` = `0`

### **Email Configuration (if needed):**
- `MAIL_SERVER` = `smtp.gmail.com`
- `MAIL_PORT` = `587`
- `MAIL_USE_TLS` = `true`
- `MAIL_USERNAME` = `your-email@gmail.com`
- `MAIL_PASSWORD` = `your-app-password`

### **Slack Integration (if needed):**
- `SLACK_BOT_TOKEN` = `xoxb-your-slack-bot-token`
- `SLACK_CHANNEL_ID` = `your-channel-id`

## 🎛️ **Using Portainer's Built-in Features**

### **Resource Management:**
- **Memory Limit**: 512MB (adjust in Portainer container settings)
- **CPU Limit**: 0.5 cores (adjust in Portainer container settings)
- **Restart Policy**: Unless-stopped (configured in compose)

### **Volume Management:**
- **guest_data**: Database storage (`/app/instance`)
- **guest_logs**: Application logs (`/app/logs`)
- **Backup Strategy**: Use Portainer's volume backup features

### **Monitoring & Health:**
- **Health Checks**: Built-in container health monitoring
- **Logs**: Real-time in Portainer → Containers → guest-management → Logs
- **Stats**: CPU/Memory usage in Portainer container view

### **Network Configuration:**
- **Port Mapping**: Change `APP_PORT` environment variable
- **Internal Network**: `guest_network` (isolated from other apps)
- **External Access**: Only through mapped port

## 🔒 **Security Best Practices**

### **Environment Variables:**
- ✅ Use Portainer's environment variable section (not the compose file)
- ✅ Generate strong `SECRET_KEY`: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
- ✅ Keep sensitive data in Portainer environment variables

### **Access Control:**
- ✅ Use Portainer's user management for team access
- ✅ Set up reverse proxy with SSL (Traefik/nginx-proxy-manager)
- ✅ Limit port exposure (only map necessary ports)

### **Data Protection:**
- ✅ Regular volume backups via Portainer
- ✅ Volume labels for organization and backup policies
- ✅ Container resource limits to prevent resource exhaustion

## 🚀 **Alternative: Local Build + Push**

If you want more control:

1. **Build locally**:
   ```bash
   cd GuestManagement
   docker build -t guest-management:latest .
   ```

2. **Export image**:
   ```bash
   docker save guest-management:latest | gzip > guest-management.tar.gz
   ```

3. **Transfer to Portainer server** and import:
   ```bash
   docker load < guest-management.tar.gz
   ```

4. **Deploy in Portainer** using the local image

## 📊 **Post-Deployment Checklist**

### **Immediate Actions:**
- [ ] Verify app loads at `http://your-server:8080`
- [ ] Check container health status (should be green)
- [ ] Verify database creation in logs
- [ ] Test basic functionality

### **Ongoing Monitoring:**
- [ ] Set up volume backup schedule
- [ ] Monitor resource usage in Portainer
- [ ] Check application logs regularly
- [ ] Update `SECRET_KEY` if using default

### **Updates:**
- [ ] Modify files locally
- [ ] Re-zip and re-upload in Portainer
- [ ] Or rebuild image and update container

## 🛠️ **Troubleshooting**

### **Database Issues:**
- Check volume permissions in container logs
- Verify `guest_data` volume is mounted correctly
- Ensure sufficient disk space

### **Permission Errors:**
- Container runs as `www-data` user
- Volumes are set with proper permissions in entrypoint
- Check Portainer volume settings

### **App Not Starting:**
- Check environment variables are set correctly
- Verify `SECRET_KEY` is not the default value
- Review container logs for specific errors

Your app is now optimized for Portainer's built-in features and private deployment! 🎉
