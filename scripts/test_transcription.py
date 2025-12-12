#!/usr/bin/env python3
"""Test script for transcription functionality.

Usage:
    # Test transcription with a sample audio file
    python scripts/test_transcription.py --file path/to/audio.flac --session test-session-123

    # Test with mock audio (generates sine wave)
    python scripts/test_transcription.py --mock --session test-session-123
"""

import argparse
import asyncio
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Import required modules
try:
    from app.services.groq_client import (
        transcribe_audio,
        TranscriptionError,
        RetryableTranscriptionError,
    )
    from app.services.database import (
        save_transcription,
        get_transcriptions_by_session,
        DatabaseError,
    )
    from app.models.schemas import TranscriptionModel
except ImportError as e:
    print(f"Import error: {e}")
    print(
        "Make sure you're running from the project root and dependencies are installed."
    )
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def create_mock_audio_file(duration: int = 5) -> Path:
    """Create a mock audio file with sine wave using FFmpeg.

    Args:
        duration: Duration in seconds.

    Returns:
        Path to the created audio file.
    """
    temp_dir = Path(tempfile.gettempdir())
    audio_file = temp_dir / f"mock_audio_{duration}s.flac"

    cmd = [
        "ffmpeg",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=440:duration={duration}",
        "-ar",
        "16000",  # Sample rate expected by Groq
        "-ac",
        "1",  # Mono
        "-c:a",
        "flac",
        "-y",  # Overwrite
        str(audio_file),
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f"Created mock audio file: {audio_file}")
        return audio_file
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create mock audio: {e}")
        if e.stderr:
            logger.error(f"FFmpeg stderr: {e.stderr.decode()}")
        raise


async def test_transcription(audio_file: Path, session_id: str) -> None:
    """Test transcription with the given audio file.

    Args:
        audio_file: Path to audio file.
        session_id: Session ID for the transcription.
    """
    print(f"\n{'=' * 60}")
    print("TRANSCRIPTION TEST")
    print(f"{'=' * 60}")
    print(f"Audio file: {audio_file}")
    print(f"File size: {audio_file.stat().st_size} bytes")
    print(f"Session ID: {session_id}")
    print(f"{'=' * 60}\n")

    try:
        # Test transcription
        print("1. Transcribing audio...")
        transcription = await transcribe_audio(audio_file, session_id)
        print(f"   ✓ Transcription successful!")
        print(
            f"   Text: {transcription.transcript[:100]}{'...' if len(transcription.transcript) > 100 else ''}"
        )

        # Test database save
        print("\n2. Saving to database...")
        transcription_id = await save_transcription(transcription)
        print(f"   ✓ Saved with ID: {transcription_id}")

        # Test database retrieval
        print("\n3. Retrieving from database...")
        saved_transcriptions = await get_transcriptions_by_session(session_id)
        print(f"   ✓ Found {len(saved_transcriptions)} transcription(s) for session")

        if saved_transcriptions:
            latest = saved_transcriptions[-1]
            print(
                f"   Latest: {latest.get('transcript', '')[:100]}{'...' if len(latest.get('transcript', '')) > 100 else ''}"
            )

        print(f"\n{'=' * 60}")
        print("TEST PASSED ✓")
        print(f"{'=' * 60}")

    except TranscriptionError as e:
        print(f"\n❌ Transcription failed: {e}")
        return False
    except DatabaseError as e:
        print(f"\n❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

    return True


async def main():
    parser = argparse.ArgumentParser(description="Test transcription functionality")
    parser.add_argument("--file", type=str, help="Path to audio file to transcribe")
    parser.add_argument("--mock", action="store_true", help="Use mock audio file")
    parser.add_argument(
        "--session", type=str, required=True, help="Session ID for transcription"
    )
    parser.add_argument(
        "--duration", type=int, default=5, help="Duration for mock audio (seconds)"
    )

    args = parser.parse_args()

    # Determine audio file
    if args.file:
        audio_file = Path(args.file)
        if not audio_file.exists():
            print(f"❌ Audio file not found: {audio_file}")
            return 1
    elif args.mock:
        print("Creating mock audio file...")
        try:
            audio_file = create_mock_audio_file(args.duration)
        except Exception as e:
            print(f"❌ Failed to create mock audio: {e}")
            return 1
    else:
        print("❌ Please specify either --file or --mock")
        return 1

    try:
        success = await test_transcription(audio_file, args.session)
        return 0 if success else 1
    finally:
        # Clean up mock file if created
        if args.mock and audio_file.exists():
            audio_file.unlink()
            print(f"Cleaned up mock file: {audio_file}")


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
