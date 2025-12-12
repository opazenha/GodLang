"""Unit tests for translation endpoints."""

import json
import pytest
from unittest.mock import patch, Mock


class TestTranslationEndpoints:
    """Test translation endpoints."""

    def test_get_translation_success(self, client, mock_mongo_client):
        """Test successful translation retrieval."""
        # Mock transcription data
        mock_transcription = {
            "_id": "test-transcription-id",
            "session_id": "test-session-id",
            "transcript": "Hello, this is a test.",
            "created_at": "2025-12-12T15:45:31Z",
        }

        # Mock translation data
        mock_translation = {
            "_id": "test-translation-id",
            "transcription_id": "test-transcription-id",
            "transcript": "Hello, this is a test.",
            "translation": "你好，这是一个测试。",
            "language": "zh",
            "created_at": "2025-12-12T15:45:35Z",
        }

        # Mock database responses
        mock_mongo_client.__getitem__.return_value.transcriptions.find_one.return_value = mock_transcription
        mock_mongo_client.__getitem__.return_value.translations.aggregate.return_value = [
            mock_translation
        ]

        response = client.get("/api/translation/test-session-id")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["transcription"]["transcript"] == "Hello, this is a test."
        assert data["data"]["translation"]["translation"] == "你好，这是一个测试。"

    def test_get_translation_no_transcription(self, client, mock_mongo_client):
        """Test translation retrieval when no transcription exists."""
        mock_mongo_client.__getitem__.return_value.transcriptions.find_one.return_value = None

        response = client.get("/api/translation/test-session-id")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"] is None
        assert "No transcriptions found" in data["message"]

    def test_get_translation_no_translation(self, client, mock_mongo_client):
        """Test translation retrieval when transcription exists but no translation."""
        # Mock transcription data
        mock_transcription = {
            "_id": "test-transcription-id",
            "session_id": "test-session-id",
            "transcript": "Hello, this is a test.",
            "created_at": "2025-12-12T15:45:31Z",
        }

        # Mock empty translation response
        mock_mongo_client.__getitem__.return_value.transcriptions.find_one.return_value = mock_transcription
        mock_mongo_client.__getitem__.return_value.translations.aggregate.return_value = []

        response = client.get("/api/translation/test-session-id")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["transcription"]["transcript"] == "Hello, this is a test."
        assert data["data"]["translation"] is None
        assert "No translations found yet" in data["message"]

    def test_get_all_translations_success(self, client, mock_mongo_client):
        """Test retrieving all translations for a session."""
        # Mock translation data
        mock_translations = [
            {
                "_id": "test-translation-id-1",
                "transcription_id": "test-transcription-id-1",
                "transcript": "Hello world.",
                "translation": "你好世界。",
                "language": "zh",
                "created_at": "2025-12-12T15:45:31Z",
            },
            {
                "_id": "test-translation-id-2",
                "transcription_id": "test-transcription-id-2",
                "transcript": "How are you?",
                "translation": "你好吗？",
                "language": "zh",
                "created_at": "2025-12-12T15:45:35Z",
            },
        ]

        mock_mongo_client.__getitem__.return_value.translations.aggregate.return_value = mock_translations

        response = client.get("/api/translation/test-session-id/all")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["count"] == 2
        assert len(data["data"]["translations"]) == 2
        assert data["data"]["session_id"] == "test-session-id"

    def test_get_all_translations_with_limit(self, client, mock_mongo_client):
        """Test retrieving translations with limit parameter."""
        mock_translations = [
            {
                "_id": "test-translation-id-1",
                "transcript": "Hello world.",
                "translation": "你好世界。",
                "language": "zh",
            }
        ]

        mock_mongo_client.__getitem__.return_value.translations.aggregate.return_value = mock_translations

        response = client.get("/api/translation/test-session-id/all?limit=1")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["count"] == 1

    def test_get_translation_database_error(self, client, mock_mongo_client):
        """Test translation retrieval with database error."""
        mock_mongo_client.__getitem__.return_value.transcriptions.find_one.side_effect = Exception(
            "Database error"
        )

        response = client.get("/api/translation/test-session-id")

        assert response.status_code == 500
        data = json.loads(response.data)
        assert data["success"] is False
        assert "Failed to get translation" in data["message"]
