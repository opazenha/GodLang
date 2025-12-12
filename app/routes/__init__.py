"""Route registration."""

from flask import Flask


def register_routes(app: Flask) -> None:
    """Register all application blueprints.

    Args:
        app: Flask application instance.
    """
    from app.routes.health import health_bp
    from app.routes.session import session_bp
    from app.routes.translation import translation_bp
    from app.routes.sse import sse_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(session_bp)
    app.register_blueprint(translation_bp)
    app.register_blueprint(sse_bp)
