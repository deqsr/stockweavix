from flask import Flask
from flask_migrate import Migrate
from markupsafe import Markup
from .config import Config
from .models import db, Employee
from .routes.inventory import inv_bp
from .routes.main import main_bp
from .routes.supplies import supplies_bp
from .routes.orders import orders_bp
from .routes.analytics import analytics_bp
from .routes.products import products_bp
from .routes.auth import auth_bp
from flask_login import LoginManager
from .routes.admin import admin_bp

login_manager = LoginManager()
login_manager.login_view = 'auth_bp.login'
login_manager.login_message = "Будь ласка, увійдіть, щоб отримати доступ до цієї сторінки."
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(employee_id):
    return db.session.get(Employee, int(employee_id))


def nl2br_filter(value: str | None) -> Markup | str:
    if value is None:
        return Markup('')
    escaped_value = str(value).replace('&', '&').replace('<', '<').replace('>', '>')
    br = Markup('<br>\n')
    processed_value = escaped_value.replace('\r\n', br).replace('\r', br).replace('\n', br)
    return processed_value


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    Migrate(app, db)

    login_manager.init_app(app)

    print("SQLALCHEMY_ENGINE_OPTIONS in app.config:", app.config.get('SQLALCHEMY_ENGINE_OPTIONS'))

    app.jinja_env.filters['nl2br'] = nl2br_filter

    app.register_blueprint(main_bp)
    app.register_blueprint(inv_bp, url_prefix='/inventory')
    app.register_blueprint(supplies_bp, url_prefix='/supplies')
    app.register_blueprint(orders_bp, url_prefix='/orders')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(products_bp, url_prefix='/products')
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    return app