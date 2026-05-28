from flask import Flask
from .extensions import login_manager, csrf


def create_app(config_object: str = "config.Config") -> Flask:
    """Application factory de Flask.

    :param config_object: ruta de importación de la clase de configuración.
    :return: instancia de Flask lista para servir.
    """
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config_object)

    login_manager.init_app(app)
    csrf.init_app(app)

    from .views.auth import bp as auth_bp
    from .views.main import bp as main_bp
    from .views.recipes import bp as recipes_bp
    from .views.users import bp as users_bp
    from .views.favorites import bp as favorites_bp
    from .views.notifications import bp as notifications_bp, unread_count_for

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(recipes_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(favorites_bp)
    app.register_blueprint(notifications_bp)

    from flask_login import current_user

    @app.context_processor
    def inject_unread():
        """Expone `unread_notifications` (int) a todas las plantillas."""
        if current_user.is_authenticated:
            return {"unread_notifications": unread_count_for(current_user.username)}
        return {"unread_notifications": 0}

    from .errors import register_error_handlers
    register_error_handlers(app)

    return app
