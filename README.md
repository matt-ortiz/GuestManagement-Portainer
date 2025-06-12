# Guest Management Flask App

A Flask-based guest management system with Docker deployment for Portainer.

## Quick Deploy to Portainer

1. **In Portainer**: Stacks → Add Stack → Repository
2. **Repository URL**: `https://github.com/YOUR_USERNAME/YOUR_REPO.git`
3. **Compose file path**: `docker-compose.yml`
4. **Environment Variables**:
   ```
   SECRET_KEY=your-secure-random-key-here
   APP_PORT=8080
   ```
5. **Deploy** and access at `http://your-server:8080`

## Configuration

### Required Environment Variables
- `SECRET_KEY` - Flask secret key (generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`)

### Optional Environment Variables
- `APP_PORT` - External port (default: 8080)
- `MAIL_SERVER` - SMTP server for email notifications
- `MAIL_USERNAME` / `MAIL_PASSWORD` - Email credentials
- `SLACK_BOT_TOKEN` / `SLACK_CHANNEL_ID` - Slack integration

## Data Persistence

- Database: Stored in `guest_data` Docker volume
- Logs: Stored in `guest_logs` Docker volume

## Local Development

```bash
cd data
pip install -r requirements.txt
python run.py
```

## Updates

Push changes to Git, then in Portainer: Stacks → your-stack → "Update the stack"
