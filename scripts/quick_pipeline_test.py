#!/usr/bin/env python3
"""Quick test script for complete pipeline with real API calls.

This script provides a simple way to test the entire pipeline:
1. Captures audio for 15 seconds
2. Processes chunks through transcription and translation
3. Shows results

Usage:
    # Test with real API calls (requires GROQ_API_KEY and MONGODB_URI)
    python scripts/quick_pipeline_test.py --session my-test-session

    # Test with mock processing
    python scripts/quick_pipeline_test.py --session my-test-session --mock
"""

import argparse
import asyncio
import logging
import os
import sys
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


async def main():
    parser = argparse.ArgumentParser(description="Quick complete pipeline test")
    parser.add_argument("--session", type=str, required=True, help="Session ID")
    parser.add_argument("--mock", action="store_true", help="Use mock processing")
    parser.add_argument(
        "--duration", type=int, default=15, help="Test duration in seconds"
    )

    args = parser.parse_args()

    # Import after path setup
    try:
        from scripts.test_complete_pipeline import run_complete_pipeline
        from app.models.schemas import LanguageCode
    except ImportError as e:
        print(f"Import error: {e}")
        return 1

    # Check environment
    if not args.mock:
        if not os.getenv("GROQ_API_KEY"):
            print(
                "❌ GROQ_API_KEY not set. Use --mock or set the environment variable."
            )
            return 1
        if not os.getenv("MONGO_URI"):
            print("❌ MONGO_URI not set. Use --mock or set the environment variable.")
            return 1

    print("🎤 Starting complete audio pipeline test...")
    print(f"   Session: {args.session}")
    print(f"   Duration: {args.duration} seconds")
    print(f"   Mode: {'Mock' if args.mock else 'Real API'}")
    print(f"   Target: Chinese (zh)")
    print("\nSpeak into your microphone now!")

    try:
        await run_complete_pipeline(
            session_id=args.session,
            target_language=LanguageCode.CHINESE,
            use_mock=args.mock,
            start_capture=True,
            duration=args.duration,
        )
        print("\n✅ Test completed successfully!")
        return 0
    except KeyboardInterrupt:
        print("\n⏹️  Test stopped by user.")
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
