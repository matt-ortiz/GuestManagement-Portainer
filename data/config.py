import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:////app/instance/guests.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session and CSRF Settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    WTF_CSRF_TIME_LIMIT = 43200  # 12 hours in seconds
    SESSION_REFRESH_EACH_REQUEST = True
