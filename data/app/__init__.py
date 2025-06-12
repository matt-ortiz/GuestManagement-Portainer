from flask import Flask
from config import Config
import os
import logging
from logging.handlers import RotatingFileHandler
from app.extensions import db, login_manager, cache, mail
from datetime import timedelta
from sqlalchemy import text

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Add these lines after app creation but before blueprint registration
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=12)
    app.config['WTF_CSRF_TIME_LIMIT'] = 43200  # 12 hours in seconds
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    cache.init_app(app)
    mail.init_app(app)

    # Set up logging
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir, exist_ok=True)
    
    # Create file handler
    file_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'guest_management.log'),
        maxBytes=10240,
        backupCount=10
    )
    
    # Set formatter
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    file_handler.setFormatter(formatter)
    
    # Set log level
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    
    # Also log to console with the same format
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    app.logger.addHandler(console_handler)
    
    app.logger.info('Guest Management startup')

    with app.app_context():
        from app.routes import main, auth, ac
        app.register_blueprint(main)
        app.register_blueprint(auth)
        app.register_blueprint(ac)
        
        # Ensure database directory exists and has proper permissions
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, mode=0o755, exist_ok=True)
                app.logger.info(f"Created database directory: {db_dir}")
        
        # Check if database exists and has tables
        try:
            # Use modern SQLAlchemy syntax
            with db.engine.connect() as conn:
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='admin';"))
                if result.fetchone() is None:
                    raise Exception("Tables don't exist")
            app.logger.info("Database tables already exist")
        except Exception as e:
            app.logger.info(f"Initializing database tables... ({str(e)})")
            try:
                db.create_all()
                app.logger.info("Database tables created successfully")
                
                # Create default admin user if no admin users exist
                from app.models import Admin
                if Admin.query.count() == 0:
                    default_admin = Admin(username='admin')
                    default_admin.set_password('admin123')  # Change this!
                    db.session.add(default_admin)
                    db.session.commit()
                    app.logger.info("Created default admin user: admin/admin123")
                    
            except Exception as create_error:
                app.logger.error(f"Failed to create database tables: {str(create_error)}")
                raise

        # Check if we need to create default admin (for existing databases)
        try:
            from app.models import Admin
            if Admin.query.count() == 0:
                default_admin = Admin(username='itadmin')
                default_admin.set_password('admin123')  # Change this!
                db.session.add(default_admin)
                db.session.commit()
                app.logger.info("Created default admin user: admin/admin123")
        except Exception as e:
            app.logger.error(f"Error creating default admin: {str(e)}")

    return app
