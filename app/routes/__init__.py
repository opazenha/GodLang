"""Route registration."""

from flask import Flask


def register_routes(app: Flask) -> None:
    """Register all application blueprints.
    
    Args:
        app: Flask application instance.
    """
    from app.routes.health import health_bp
    
    app.register_blueprint(health_bp)
