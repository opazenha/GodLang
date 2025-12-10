"""MongoDB database service."""

from flask import Flask
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure


def init_db(app: Flask) -> None:
    """Initialize MongoDB connection.
    
    Args:
        app: Flask application instance.
    """
    mongo_uri = app.config.get("MONGO_URI")
    
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # Verify connection
        client.admin.command("ping")
        app.mongo_client = client
        app.db = client[app.config.get("MONGO_DB_NAME", "godlang")]
        app.logger.info("Connected to MongoDB")
    except ConnectionFailure as e:
        app.logger.error(f"Failed to connect to MongoDB: {e}")
        app.mongo_client = None
        app.db = None


def get_db():
    """Get database instance from current app context.
    
    Returns:
        MongoDB database instance or None.
    """
    from flask import current_app
    return getattr(current_app, "db", None)
