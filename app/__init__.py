from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import timedelta
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
bcrypt = Bcrypt()
limiter = Limiter(get_remote_address)

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.permanent_session_lifetime = timedelta(minutes=10)  # Auto-logout after 10 mins

    db.init_app(app)
    bcrypt.init_app(app)

    limiter.init_app(app)

    from app.routes import main
    app.register_blueprint(main)

    print("✅ Blueprint registered successfully!")

    return app
