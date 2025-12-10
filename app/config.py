"""Application configuration."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
    
    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "godlang")
    
    # Groq API
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    # Audio Processing
    AUDIO_CHUNK_DURATION_MS = int(os.getenv("AUDIO_CHUNK_DURATION_MS", "5000"))


class DevelopmentConfig(Config):
    """Development configuration."""
    
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    
    DEBUG = False


# Configuration mapping
config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
