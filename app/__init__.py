"""Flask application factory."""

from flask import Flask

from app.config import Config
from app.routes import register_routes


def create_app(config_class: type = Config) -> Flask:
    """Create and configure the Flask application.
    
    Args:
        config_class: Configuration class to use.
        
    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions and clients
    _init_extensions(app)
    
    # Register blueprints
    register_routes(app)
    
    return app


def _init_extensions(app: Flask) -> None:
    """Initialize Flask extensions and external clients.
    
    Args:
        app: Flask application instance.
    """
    from app.services.database import init_db
    from app.services.groq_client import init_groq
    
    init_db(app)
    init_groq(app)
