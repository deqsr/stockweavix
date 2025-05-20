from flask import Flask
from flask_migrate import Migrate
from .config import Config
from .models import db
from .routes.inventory import inv_bp
from .routes.main import main_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # SQLAlchemy + міграції
    db.init_app(app)
    Migrate(app, db)

    # blueprints
    app.register_blueprint(inv_bp, url_prefix='/inventory')
    app.register_blueprint(main_bp)

    return app
