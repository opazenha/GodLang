"""Test configuration and fixtures."""

import os
import pytest
from unittest.mock import Mock, patch
from pymongo import MongoClient

from app import create_app
from app.config import DevelopmentConfig


@pytest.fixture(scope="session")
def test_mongo_uri():
    """Get test MongoDB URI."""
    # Use test database to avoid interfering with development data
    return os.getenv("TEST_MONGO_URI", "mongodb://localhost:27017/test_godlang")


@pytest.fixture(scope="session")
def test_app(test_mongo_uri):
    """Create test Flask application."""

    # Override config for testing
    class TestConfig(DevelopmentConfig):
        TESTING = True
        MONGO_URI = test_mongo_uri
        MONGO_DB_NAME = "test_godlang"
        GROQ_API_KEY = "test-key"  # Mock key for testing

    app = create_app(TestConfig)
    with app.app_context():
        yield app


@pytest.fixture
def client(test_app):
    """Create test client."""
    return test_app.test_client()


@pytest.fixture
def mock_mongo_client():
    """Mock MongoDB client for unit tests."""
    with patch("app.services.database.MongoClient") as mock_client:
        # Mock the client and database
        mock_instance = Mock()
        mock_client.return_value = mock_instance

        # Mock database and collections
        mock_db = Mock()
        mock_instance.__getitem__.return_value = mock_db

        # Mock admin command for ping
        mock_instance.admin.command.return_value = {"ok": 1}

        yield mock_instance


@pytest.fixture
def mock_groq_client():
    """Mock Groq client for unit tests."""
    with patch("app.services.groq_client.Groq") as mock_groq:
        mock_instance = Mock()
        mock_groq.return_value = mock_instance

        # Mock chat completions
        mock_chat = Mock()
        mock_instance.chat.completions.create = mock_chat

        yield mock_chat


@pytest.fixture
def sample_session_data():
    """Sample session data for testing."""
    return {"language": "zh"}


@pytest.fixture
def sample_transcription_data():
    """Sample transcription data for testing."""
    return {
        "session_id": "test-session-id",
        "transcript": "Hello, this is a test transcription.",
    }


@pytest.fixture
def sample_translation_data():
    """Sample translation data for testing."""
    return {
        "transcription_id": "test-transcription-id",
        "transcript": "Hello, this is a test transcription.",
        "translation": "你好，这是一个测试转录。",
        "language": "zh",
    }


@pytest.fixture(autouse=True)
def cleanup_test_db(test_mongo_uri):
    """Clean up test database after each test."""
    # Clean up before test
    client = MongoClient(test_mongo_uri)
    db = client["test_godlang"]

    # Drop collections if they exist
    for collection_name in ["sessions", "transcriptions", "translations"]:
        if collection_name in db.list_collection_names():
            db[collection_name].drop()

    yield

    # Clean up after test
    for collection_name in ["sessions", "transcriptions", "translations"]:
        if collection_name in db.list_collection_names():
            db[collection_name].drop()

    client.close()
