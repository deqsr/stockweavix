from flask import Flask
from flask_migrate import Migrate
from .config import Config
from .models import db
from .routes.inventory import inv_bp
from .routes.main import main_bp
from .routes.supplies import supplies_bp
from .routes.orders import orders_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # SQLAlchemy + міграції
    db.init_app(app)
    Migrate(app, db)
    print("SQLALCHEMY_ENGINE_OPTIONS in app.config:", app.config.get('SQLALCHEMY_ENGINE_OPTIONS'))
    # blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(inv_bp, url_prefix='/inventory')
    app.register_blueprint(supplies_bp, url_prefix='/supplies')
    app.register_blueprint(orders_bp, url_prefix='/orders')


    return app
