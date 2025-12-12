#!/usr/bin/env python3
"""Test script for audio pipeline.

Usage:
    # Show FFmpeg command (run this in a separate terminal)
    python scripts/test_audio_pipeline.py --show-command

    # List audio devices
    python scripts/test_audio_pipeline.py --list-devices

    # Run pipeline with mock processing (watch for files)
    python scripts/test_audio_pipeline.py --run

    # Run pipeline with FFmpeg capture (full test)
    python scripts/test_audio_pipeline.py --run --capture
"""

import argparse
import asyncio
import logging
import os
import subprocess
import sys

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Import config module directly (not through app package to avoid Flask)
import importlib.util

spec = importlib.util.spec_from_file_location(
    "config", os.path.join(PROJECT_ROOT, "app", "config.py")
)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
AudioConfig = config_module.AudioConfig

# Import audio module directly
spec2 = importlib.util.spec_from_file_location(
    "audio", os.path.join(PROJECT_ROOT, "app", "services", "audio.py")
)
audio_module = importlib.util.module_from_spec(spec2)
# Inject AudioConfig into audio module's namespace before loading
sys.modules["app.config"] = config_module
spec2.loader.exec_module(audio_module)

AudioChunk = audio_module.AudioChunk
AudioPipeline = audio_module.AudioPipeline
DirectoryManager = audio_module.DirectoryManager
get_ffmpeg_command = audio_module.get_ffmpeg_command
list_audio_devices = audio_module.list_audio_devices

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


async def mock_transcribe(chunk) -> None:
    """Mock transcription function for testing."""
    logger.info(f"[MOCK] Transcribing: {chunk.filename}")
    logger.info(f"[MOCK] File size: {chunk.path.stat().st_size} bytes")
    await asyncio.sleep(1)  # Simulate API call
    logger.info(f"[MOCK] Transcription complete: {chunk.filename}")


async def real_transcribe(chunk, session_id: str = "test-session") -> None:
    """Real transcription function using Groq API."""
    try:
        # Import here to avoid issues when dependencies aren't available
        from app.services.audio import process_audio_chunk_transcription

        await process_audio_chunk_transcription(chunk, session_id)
    except ImportError as e:
        logger.error(f"Cannot import transcription services: {e}")
        logger.error(
            "Make sure all dependencies are installed: pip install -r requirements.txt"
        )
        raise


async def run_pipeline(
    start_capture: bool = False,
    use_real_transcription: bool = False,
    session_id: str = "test-session",
) -> None:
    """Run the audio pipeline."""
    if use_real_transcription:
        pipeline = AudioPipeline(
            process_fn=lambda chunk: real_transcribe(chunk, session_id)
        )
    else:
        pipeline = AudioPipeline(process_fn=mock_transcribe)

    print("\n" + "=" * 60)
    print("AUDIO PIPELINE TEST")
    print("=" * 60)
    print(f"Temp directory: {AudioConfig.get_temp_dir()}")
    print(f"Chunk duration: {AudioConfig.CHUNK_DURATION}s")
    print(f"Sample rate: {AudioConfig.SAMPLE_RATE}Hz")
    print(f"Max retries: {AudioConfig.MAX_RETRIES}")
    print("=" * 60)

    if not start_capture:
        print("\nFFmpeg command (run in separate terminal):")
        print("-" * 60)
        print(pipeline.get_ffmpeg_command())
        print("-" * 60)

    print("\nStarting pipeline... Press Ctrl+C to stop.\n")

    try:
        await pipeline.start(start_capture=start_capture)

        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n\nShutting down...")
    finally:
        await pipeline.stop()
        print("Pipeline stopped.")


def show_ffmpeg_command() -> None:
    """Show the FFmpeg command for manual execution."""
    cmd = get_ffmpeg_command()
    print("\nFFmpeg capture command:")
    print("-" * 60)
    print(cmd)
    print("-" * 60)
    print("\nRun this command in a separate terminal to start capturing audio.")
    print(f"Audio chunks will be written to: {AudioConfig.get_temp_dir() / 'pending'}")


def show_list_devices() -> None:
    """Show command to list audio devices."""
    cmd = list_audio_devices()
    print("\nCommand to list audio devices:")
    print("-" * 60)
    print(cmd)
    print("-" * 60)
    print("\nRunning command...\n")

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            # FFmpeg outputs device list to stderr
            print(result.stderr)
    except Exception as e:
        print(f"Error running command: {e}")


def setup_dirs() -> None:
    """Setup directories only."""
    dm = DirectoryManager()
    dm.setup()
    print(f"\nDirectories created at: {AudioConfig.get_temp_dir()}")
    for name, path in dm.dirs.items():
        print(f"  - {name}: {path}")


def main():
    parser = argparse.ArgumentParser(description="Test audio pipeline")
    parser.add_argument(
        "--show-command", action="store_true", help="Show FFmpeg command"
    )
    parser.add_argument(
        "--list-devices", action="store_true", help="List audio devices"
    )
    parser.add_argument("--setup", action="store_true", help="Setup directories only")
    parser.add_argument("--run", action="store_true", help="Run the pipeline")
    parser.add_argument(
        "--capture", action="store_true", help="Also start FFmpeg capture"
    )
    parser.add_argument(
        "--real-transcription",
        action="store_true",
        help="Use real Groq transcription instead of mock",
    )
    parser.add_argument(
        "--session",
        type=str,
        default="test-session",
        help="Session ID for transcriptions",
    )

    args = parser.parse_args()

    if args.show_command:
        show_ffmpeg_command()
    elif args.list_devices:
        show_list_devices()
    elif args.setup:
        setup_dirs()
    elif args.run:
        asyncio.run(
            run_pipeline(
                start_capture=args.capture,
                use_real_transcription=args.real_transcription,
                session_id=args.session,
            )
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
