from datetime import datetime
from app.extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import pytz
import json

@login_manager.user_loader
def load_user(id):
    return Admin.query.get(int(id))

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Guest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100))
    host = db.Column(db.String(100))
    additional_guests = db.Column(db.Text)  # Stored as JSON string
    timestamp = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(pytz.UTC))
    notifications = db.Column(db.Text)  # JSON: [{"type": "slack/email", "time": "UTC timestamp"}]

    def add_notification(self, notification_type):
        """Add a new notification record"""
        current_notifications = []
        if self.notifications:
            try:
                current_notifications = json.loads(self.notifications)
            except json.JSONDecodeError:
                current_notifications = []
        
        current_notifications.append({
            "type": notification_type,
            "time": datetime.now(pytz.UTC).isoformat()
        })
        self.notifications = json.dumps(current_notifications)

    def get_notifications(self):
        """Get list of notifications"""
        if not self.notifications:
            return []
        try:
            return json.loads(self.notifications)
        except json.JSONDecodeError:
            return []

class TeamMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    slack_notifications = db.Column(db.Boolean, default=False)
    email_notifications = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<TeamMember {self.name}>'

class SystemSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(500))
    
    @classmethod
    def get_setting(cls, key, default=None):
        setting = cls.query.filter_by(key=key).first()
        return setting.value if setting else default

    @classmethod
    def set_setting(cls, key, value):
        setting = cls.query.filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            setting = cls(key=key, value=value)
            db.session.add(setting)
        db.session.commit() 

class SessionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(128), nullable=False)
    user_agent = db.Column(db.String(256))
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    form_interactions = db.Column(db.Integer, default=0)
    submission_attempts = db.Column(db.Integer, default=0)
    errors = db.Column(db.Text)