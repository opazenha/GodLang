"""Pydantic schemas for data validation."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    model_config = ConfigDict(
        # Use enum values instead of names in serialization
        use_enum_values=True,
        # Validate on assignment
        validate_assignment=True,
        # Allow population by field name or alias
        populate_by_name=True,
        # Strip whitespace from strings
        str_strip_whitespace=True,
    )


class LanguageCode(str, Enum):
    """Supported language codes."""
    
    CHINESE = "zh"
    # Future languages can be added here


class SessionStatus(str, Enum):
    """Session status values."""
    
    ACTIVE = "active"
    CLOSED = "closed"


# --- Response Schemas ---

class HealthResponse(BaseSchema):
    """Health check response schema."""
    
    status: str = Field(..., description="Overall health status")
    mongo_connected: bool = Field(..., description="MongoDB connection status")
    ffmpeg_installed: bool = Field(..., description="FFmpeg availability status")


class APIResponse(BaseSchema):
    """Standard API response wrapper."""
    
    success: bool = Field(..., description="Whether the request succeeded")
    message: Optional[str] = Field(None, description="Optional message")
    data: Optional[dict] = Field(None, description="Response data")


# --- Session Schemas ---

class SessionCreate(BaseSchema):
    """Schema for creating a new session."""
    
    language: LanguageCode = Field(
        default=LanguageCode.CHINESE,
        description="Target translation language"
    )


class SessionResponse(BaseSchema):
    """Schema for session response."""
    
    id: str = Field(..., description="Session ID")
    language: LanguageCode = Field(..., description="Target language")
    status: SessionStatus = Field(..., description="Session status")
    created_at: datetime = Field(..., description="Creation timestamp")


# --- Transcription Schemas ---

class TranscriptionModel(BaseSchema):
    """Transcription data schema."""
    
    id: Optional[str] = Field(None, description="Transcription ID")
    session_id: str = Field(..., description="Parent session ID")
    transcript: str = Field(..., description="Transcribed text in English")
    created_at: datetime = Field(default_factory=datetime.utcnow)


# --- Translation Schemas ---

class TranslationModel(BaseSchema):
    """Translation data schema."""
    
    id: Optional[str] = Field(None, description="Translation ID")
    transcription_id: str = Field(..., description="Parent transcription ID")
    transcript: str = Field(..., description="Original English text")
    translation: str = Field(..., description="Translated text")
    language: LanguageCode = Field(..., description="Target language")
    created_at: datetime = Field(default_factory=datetime.utcnow)
