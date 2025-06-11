from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS
from flask_caching import Cache
from flask_mail import Mail

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
cache = Cache(config={
    'CACHE_TYPE': 'null',
    'CACHE_NO_NULL_WARNING': True
})
mail = Mail() 