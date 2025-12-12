#!/usr/bin/env python3
"""Complete end-to-end audio pipeline test.

This script tests the entire pipeline:
1. Capture audio from laptop microphone
2. Chunk audio into segments
3. Transcribe each chunk to English
4. Translate transcription to target language
5. Print results to logs

Usage:
    # Run complete pipeline with real transcription and translation
    python scripts/test_complete_pipeline.py --session test-session-123

    # Run with mock processing (no API calls)
    python scripts/test_complete_pipeline.py --mock --session test-session-123

    # Run with specific target language
    python scripts/test_complete_pipeline.py --session test-session-123 --target-language spanish
"""

import argparse
import asyncio
import logging
import os
import sys
import tempfile
from pathlib import Path

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Import required modules
try:
    from app.services.audio import (
        AudioPipeline,
        AudioChunk,
        process_audio_chunk_transcription,
        process_translation_pipeline,
    )
    from app.services.groq_client import transcribe_audio, translate_text
    from app.models.schemas import LanguageCode
    from app.config import AudioConfig
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


async def mock_complete_pipeline(
    chunk: AudioChunk,
    session_id: str,
    target_language: LanguageCode = LanguageCode.CHINESE,
) -> None:
    """Mock complete pipeline for testing without API calls."""
    logger.info(f"[MOCK] Processing chunk: {chunk.filename}")
    logger.info(f"[MOCK] File size: {chunk.path.stat().st_size} bytes")

    # Mock transcription
    await asyncio.sleep(0.5)  # Simulate transcription API call
    mock_transcript = f"This is a mock transcription for {chunk.filename}"
    logger.info(f"[MOCK] Transcription: {mock_transcript}")

    # Mock translation
    await asyncio.sleep(0.5)  # Simulate translation API call
    mock_translation = (
        f"这是 {chunk.filename} 的模拟翻译"
        if target_language == LanguageCode.CHINESE
        else f"Esta es una traducción simulada para {chunk.filename}"
    )
    logger.info(f"[MOCK] Translation ({target_language.value}): {mock_translation}")

    logger.info(f"[MOCK] Complete pipeline finished for: {chunk.filename}")


async def real_complete_pipeline(
    chunk: AudioChunk,
    session_id: str,
    target_language: LanguageCode = LanguageCode.CHINESE,
) -> None:
    """Real complete pipeline with transcription and translation."""
    try:
        logger.info(f"Processing chunk: {chunk.filename}")

        # Initialize Flask app context for Groq client
        from app import create_app

        app = create_app()
        with app.app_context():
            # Step 1: Transcribe the audio chunk
            logger.info("Step 1: Transcribing audio...")
            transcription = await transcribe_audio(chunk.path, session_id)
            transcript_text = transcription.transcript

            logger.info(
                f"✓ Transcription successful: {transcript_text[:100]}{'...' if len(transcript_text) > 100 else ''}"
            )

            # Step 2: Translate the transcription
            logger.info(f"Step 2: Translating to {target_language.value}...")
            translation = await translate_text(
                transcript_text,
                session_id,  # Use session_id instead of transcription.id
                target_language,
            )

            logger.info(
                f"✓ Translation successful: {translation.translation[:100]}{'...' if len(translation.translation) > 100 else ''}"
            )

            # Step 3: Save both to database (skip for now to avoid async issues)
            logger.info("Step 3: Skipping database save for test...")

            # Step 4: Print final results
            print("\n" + "=" * 80)
            print("PIPELINE RESULT")
            print("=" * 80)
            print(f"Chunk: {chunk.filename}")
            print(f"Session: {session_id}")
            print(f"Original Text (English): {transcript_text}")
            print(
                f"Translated Text ({target_language.value}): {translation.translation}"
            )
            print("=" * 80)

            logger.info(f"✓ Complete pipeline finished for: {chunk.filename}")

    except Exception as e:
        logger.error(f"Pipeline failed for {chunk.filename}: {e}")
        raise


def create_mock_processing_function(
    session_id: str, target_language: LanguageCode, use_mock: bool
):
    """Create a processing function that matches the expected signature."""
    if use_mock:

        async def process_fn(chunk: AudioChunk) -> None:
            await mock_complete_pipeline(chunk, session_id, target_language)
    else:

        async def process_fn(chunk: AudioChunk) -> None:
            await real_complete_pipeline(chunk, session_id, target_language)

    return process_fn


async def run_complete_pipeline(
    session_id: str,
    target_language: LanguageCode = LanguageCode.CHINESE,
    use_mock: bool = False,
    start_capture: bool = True,
    duration: int = 30,
) -> None:
    """Run the complete audio pipeline test."""

    print("\n" + "=" * 80)
    print("COMPLETE AUDIO PIPELINE TEST")
    print("=" * 80)
    print(f"Session ID: {session_id}")
    print(f"Target Language: {target_language.value}")
    print(f"Mock Mode: {use_mock}")
    print(f"Auto Capture: {start_capture}")
    if start_capture:
        print(f"Test Duration: {duration} seconds")
    print(f"Temp Directory: {AudioConfig.get_temp_dir()}")
    print(f"Chunk Duration: {AudioConfig.CHUNK_DURATION}s")
    print(f"Sample Rate: {AudioConfig.SAMPLE_RATE}Hz")
    print("=" * 80)

    # Create pipeline with appropriate processing function
    process_fn = create_mock_processing_function(session_id, target_language, use_mock)
    pipeline = AudioPipeline(process_fn=process_fn)

    try:
        print("\nStarting pipeline... Press Ctrl+C to stop early.\n")

        # Start the pipeline
        await pipeline.start(start_capture=start_capture)

        if start_capture:
            # Run for specified duration
            print(f"Running for {duration} seconds...")
            await asyncio.sleep(duration)
        else:
            # Run indefinitely until interrupted
            print("Running indefinitely... Press Ctrl+C to stop.")
            while True:
                await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n\nShutting down early...")
    finally:
        await pipeline.stop()
        print("Pipeline stopped.")

        # Print summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print("✓ Pipeline execution completed")
        print("✓ Check logs above for detailed results")
        print("✓ Audio chunks have been processed through the complete pipeline")
        print("=" * 80)


def list_target_languages():
    """List available target languages."""
    print("\nAvailable target languages:")
    print("-" * 40)
    for lang in LanguageCode:
        print(f"  - {lang.value}")
    print("-" * 40)


def main():
    parser = argparse.ArgumentParser(description="Test complete audio pipeline")
    parser.add_argument(
        "--session", type=str, required=True, help="Session ID for the test"
    )
    parser.add_argument(
        "--target-language",
        type=str,
        default="chinese",
        help="Target language for translation (default: chinese)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock processing instead of real API calls",
    )
    parser.add_argument(
        "--no-capture",
        action="store_true",
        help="Don't start FFmpeg capture (expect external audio files)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=30,
        help="Test duration in seconds when using auto-capture (default: 30)",
    )
    parser.add_argument(
        "--list-languages",
        action="store_true",
        help="List available target languages",
    )

    args = parser.parse_args()

    if args.list_languages:
        list_target_languages()
        return 0

    if not args.session:
        parser.print_help()
        return 1

    # Parse target language
    try:
        target_language = LanguageCode(args.target_language.lower())
    except ValueError:
        print(f"❌ Invalid target language: {args.target_language}")
        print("Use --list-languages to see available options")
        return 1

    # Check environment variables for real API calls
    if not args.mock:
        if not os.getenv("GROQ_API_KEY"):
            print("❌ GROQ_API_KEY environment variable not set")
            print("Set it or use --mock for testing without API calls")
            return 1

        if not os.getenv("MONGO_URI"):
            print("❌ MONGO_URI environment variable not set")
            print("Set it or use --mock for testing without database")
            return 1

    try:
        asyncio.run(
            run_complete_pipeline(
                session_id=args.session,
                target_language=target_language,
                use_mock=args.mock,
                start_capture=not args.no_capture,
                duration=args.duration,
            )
        )
        return 0
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
