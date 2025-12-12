#!/usr/bin/env python3
"""Test script for translation functionality.

Usage:
    # Test translation with sample text
    python scripts/test_translation.py --text "Hello, how are you?" --transcription-id test-123

    # Test with mock transcription (creates and translates)
    python scripts/test_translation.py --mock --session test-session-456
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
logger = logging.getLogger(__name__)


async def test_translation(text: str, transcription_id: str) -> bool:
    """Test translation with given text.

    Args:
        text: English text to translate.
        transcription_id: ID for the transcription.

    Returns:
        True if successful, False otherwise.
    """
    print(f"\n{'=' * 60}")
    print("TRANSLATION TEST")
    print(f"{'=' * 60}")
    print(f"Text: {text}")
    print(f"Length: {len(text)} characters")
    print(f"Transcription ID: {transcription_id}")
    print(f"{'=' * 60}\n")

    # Get API key from environment
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your-groq-api-key-here":
        print("❌ GROQ_API_KEY not configured or still placeholder")
        print("Please set a valid Groq API key in your .env file")
        return False

    try:
        # Import required modules
        from groq import Groq
        from app.models.schemas import LanguageCode

        # Initialize client
        client = Groq(api_key=api_key)
        print("✓ Groq client initialized")

        # Translate
        print("1. Translating text...")

        # Optimized prompt for high-quality translation
        system_prompt = f"""You are a professional translator specializing in English to {LanguageCode.CHINESE.value} translation.
        
Your task is to translate the given English text into natural, accurate {LanguageCode.CHINESE.value}.
Follow these guidelines:
- Preserve the original meaning and tone
- Use natural, fluent {LanguageCode.CHINESE.value} expressions
- Maintain proper grammar and syntax
- For technical terms, use appropriate {LanguageCode.CHINESE.value} equivalents
- Do not add explanations or notes - only return the translation
- If the text contains multiple sentences, translate all of them
- Keep the same level of formality as the original text"""

        user_prompt = (
            f"Translate this English text to {LanguageCode.CHINESE.value}:\n\n{text}"
        )

        response = client.chat.completions.create(
            model="qwen/qwen3-32b",  # Qwen 3 32B for high-quality translation
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,  # Lower temperature for consistent translation
            max_tokens=2048,  # Sufficient for most translations
        )

        translation_text = response.choices[0].message.content

        if not translation_text or not translation_text.strip():
            print("❌ Empty translation result")
            return False

        print(f"✓ Translation successful!")
        print(f"   Original: {text}")
        print(f"   Translation: {translation_text}")
        print(f"   Length: {len(translation_text)} characters")

        print(f"\n{'=' * 60}")
        print("TEST PASSED ✓")
        print(f"{'=' * 60}")
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


async def test_with_mock_transcription(session_id: str) -> bool:
    """Test translation with a mock transcription.

    Args:
        session_id: Session ID for mock transcription.

    Returns:
        True if successful, False otherwise.
    """
    print("Creating mock transcription...")

    # Sample English text for translation
    sample_text = "Hello, this is a test of the translation system. We are checking if English to Chinese translation works correctly with the Qwen 3 32B model."

    return await test_translation(sample_text, f"mock-{session_id}")


async def main() -> int:
    """Main function to handle command line arguments and run tests."""
    parser = argparse.ArgumentParser(description="Test translation functionality")
    parser.add_argument("--text", type=str, help="English text to translate")
    parser.add_argument("--transcription-id", type=str, help="Transcription ID")
    parser.add_argument("--mock", action="store_true", help="Use mock transcription")
    parser.add_argument("--session", type=str, help="Session ID for mock transcription")

    args = parser.parse_args()

    # Determine test mode
    if args.text and args.transcription_id:
        success = await test_translation(args.text, args.transcription_id)
    elif args.mock and args.session:
        success = await test_with_mock_transcription(args.session)
    else:
        print("❌ Please specify either:")
        print("  --text and --transcription-id, OR")
        print("  --mock and --session")
        return 1

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
