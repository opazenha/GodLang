"""Groq API client service."""

from flask import Flask
from groq import Groq


def init_groq(app: Flask) -> None:
    """Initialize Groq API client.
    
    Args:
        app: Flask application instance.
    """
    api_key = app.config.get("GROQ_API_KEY")
    
    if not api_key:
        app.logger.warning("GROQ_API_KEY not configured")
        app.groq_client = None
        return
    
    app.groq_client = Groq(api_key=api_key)
    app.logger.info("Groq client initialized")


def get_groq_client() -> Groq | None:
    """Get Groq client from current app context.
    
    Returns:
        Groq client instance or None.
    """
    from flask import current_app
    return getattr(current_app, "groq_client", None)
