"""Application configuration."""

import os
import platform
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class AudioConfig:
    """Audio processing configuration."""
    
    # Chunk settings
    CHUNK_DURATION = int(os.getenv("AUDIO_CHUNK_DURATION", "10"))  # seconds
    SAMPLE_RATE = int(os.getenv("AUDIO_SAMPLE_RATE", "16000"))  # Hz
    CHANNELS = 1  # mono
    FORMAT = "wav"
    
    # Retry and cleanup
    MAX_RETRIES = int(os.getenv("AUDIO_MAX_RETRIES", "3"))
    STABILITY_WAIT = float(os.getenv("AUDIO_STABILITY_WAIT", "2.0"))  # seconds
    CLEANUP_INTERVAL = int(os.getenv("AUDIO_CLEANUP_INTERVAL", "300"))  # 5 minutes
    FILE_TTL = int(os.getenv("AUDIO_FILE_TTL", "1800"))  # 30 minutes
    
    # Directories
    PENDING_DIR = "pending"
    PROCESSING_DIR = "processing"
    FAILED_DIR = "failed"
    
    @classmethod
    def get_temp_dir(cls) -> Path:
        """Get platform-specific temp directory."""
        custom_dir = os.getenv("AUDIO_TEMP_DIR")
        if custom_dir:
            return Path(custom_dir)
        if platform.system() == "Windows":
            return Path("C:/Temp/godlang")
        return Path("/tmp/godlang")
    
    @classmethod
    def get_audio_input(cls) -> tuple[str, str]:
        """Get platform-specific FFmpeg audio input (format, device)."""
        if platform.system() == "Windows":
            device = os.getenv("AUDIO_DEVICE", "Mixing Board")
            return ("dshow", f"audio={device}")
        # Linux: Use PipeWire/PulseAudio - 'default' works for both
        device = os.getenv("AUDIO_DEVICE", "default")
        return ("pulse", device)  # FFmpeg uses 'pulse' for both PulseAudio and PipeWire
    
    @classmethod
    def get_all_dirs(cls) -> dict[str, Path]:
        """Get all audio processing directories."""
        base = cls.get_temp_dir()
        return {
            "pending": base / cls.PENDING_DIR,
            "processing": base / cls.PROCESSING_DIR,
            "failed": base / cls.FAILED_DIR,
        }


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
