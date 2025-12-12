#!/usr/bin/env python3
"""Simple standalone test for Groq transcription.

Usage:
    python scripts/test_groq_simple.py --file path/to/audio.flac
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def create_mock_audio_file(duration: int = 5) -> Path:
    """Create a mock audio file with sine wave using FFmpeg."""
    temp_dir = Path(tempfile.gettempdir())
    audio_file = temp_dir / f"mock_audio_{duration}s.flac"

    cmd = [
        "ffmpeg",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=440:duration={duration}",
        "-ar",
        "16000",
        "-ac",
        "1",
        "-c:a",
        "flac",
        "-y",
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


async def test_groq_transcription(audio_file: Path) -> None:
    """Test Groq transcription directly."""
    print(f"\n{'=' * 60}")
    print("GROQ TRANSCRIPTION TEST")
    print(f"{'=' * 60}")
    print(f"Audio file: {audio_file}")
    print(f"File size: {audio_file.stat().st_size} bytes")
    print(f"{'=' * 60}\n")

    # Get API key from environment
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your-groq-api-key-here":
        print("❌ GROQ_API_KEY not configured or still placeholder")
        print("Please set a valid Groq API key in your .env file")
        return False

    try:
        # Import Groq
        from groq import Groq

        # Initialize client
        client = Groq(api_key=api_key)
        print("✓ Groq client initialized")

        # Transcribe
        print("1. Transcribing audio...")
        with open(audio_file, "rb") as file:
            response = client.audio.transcriptions.create(
                file=(audio_file.name, file.read()),
                model="whisper-large-v3-turbo",
                response_format="text",
                temperature=0.0,
            )

        transcript_text = response if isinstance(response, str) else str(response)

        if not transcript_text or not transcript_text.strip():
            print("❌ Empty transcription result")
            return False

        print(f"✓ Transcription successful!")
        print(
            f"   Text: {transcript_text[:200]}{'...' if len(transcript_text) > 200 else ''}"
        )
        print(f"   Length: {len(transcript_text)} characters")

        print(f"\n{'=' * 60}")
        print("TEST PASSED ✓")
        print(f"{'=' * 60}")
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


async def main():
    parser = argparse.ArgumentParser(description="Test Groq transcription")
    parser.add_argument("--file", type=str, help="Path to audio file to transcribe")
    parser.add_argument("--mock", action="store_true", help="Use mock audio file")
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
        success = await test_groq_transcription(audio_file)
        return 0 if success else 1
    finally:
        # Clean up mock file if created
        if args.mock and audio_file.exists():
            audio_file.unlink()
            print(f"Cleaned up mock file: {audio_file}")


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
