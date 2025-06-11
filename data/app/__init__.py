from flask import Flask
from config import Config
import os
import logging
from logging.handlers import RotatingFileHandler
from app.extensions import db, login_manager, cache, mail
from datetime import timedelta

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
        os.makedirs(logs_dir)
    
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
        try:
            db.engine.execute('SELECT 1 FROM admin')
        except Exception as e:
            app.logger.info("Initializing database tables...")
            os.makedirs(os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')), exist_ok=True)
            db.create_all()
            app.logger.info("Database tables created successfully")

    return app