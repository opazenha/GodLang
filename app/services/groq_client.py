"""Groq API client service."""

import logging
from pathlib import Path
from typing import Optional

from flask import Flask
from groq import Groq

from app.models.schemas import TranscriptionModel

logger = logging.getLogger(__name__)


class TranscriptionError(Exception):
    """Transcription service error."""

    pass


class RetryableTranscriptionError(TranscriptionError):
    """Retryable transcription error."""

    pass


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


async def transcribe_audio(
    audio_file: Path,
    session_id: str,
    language: Optional[str] = None,
) -> TranscriptionModel:
    """Transcribe audio file to English using Groq Whisper API.

    Args:
        audio_file: Path to audio file to transcribe.
        session_id: Session ID for the transcription.
        language: Optional source language code (auto-detect if None).

    Returns:
        TranscriptionModel with the transcribed text.

    Raises:
        TranscriptionError: If transcription fails permanently.
        RetryableTranscriptionError: If transcription failed but can be retried.
    """
    client = get_groq_client()
    if not client:
        raise TranscriptionError("Groq client not initialized")

    if not audio_file.exists():
        raise TranscriptionError(f"Audio file not found: {audio_file}")

    try:
        logger.info(f"Transcribing {audio_file.name} for session {session_id}")

        with open(audio_file, "rb") as file:
            # Use Groq's Whisper API with translation to English
            response = client.audio.transcriptions.create(
                file=(audio_file.name, file.read()),
                model="whisper-large-v3-turbo",
                language=language,  # None for auto-detect
                response_format="text",
                temperature=0.0,  # Lower temperature for more consistent output
            )

        # Groq returns text directly when response_format="text"
        transcript_text = response if isinstance(response, str) else str(response)

        if not transcript_text or not transcript_text.strip():
            raise RetryableTranscriptionError("Empty transcription result")

        logger.info(f"Transcription successful: {len(transcript_text)} characters")

        return TranscriptionModel(
            session_id=session_id,
            transcript=transcript_text.strip(),
        )

    except Exception as e:
        error_msg = str(e)

        # Check for retryable errors
        retryable_patterns = [
            "rate limit",
            "timeout",
            "connection",
            "network",
            "temporary",
            "service unavailable",
            "internal server error",
        ]

        if any(pattern in error_msg.lower() for pattern in retryable_patterns):
            logger.warning(
                f"Retryable transcription error for {audio_file.name}: {error_msg}"
            )
            raise RetryableTranscriptionError(error_msg) from e

        logger.error(f"Transcription failed for {audio_file.name}: {error_msg}")
        raise TranscriptionError(error_msg) from e
