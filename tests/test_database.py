"""Unit tests for database operations."""

import pytest
from unittest.mock import Mock, patch
from pymongo.errors import PyMongoError

from app.models.schemas import (
    SessionModel,
    TranscriptionModel,
    TranslationModel,
    LanguageCode,
    SessionStatus,
)
from app.services.database import (
    save_session,
    get_session,
    update_session_status,
    save_transcription,
    get_transcriptions_by_session,
    get_latest_transcription,
    save_translation,
    get_translations_by_transcription,
)


class TestDatabaseOperations:
    """Test database operations."""

    def test_save_session_success(self, mock_mongo_client):
        """Test successful session save."""
        # Mock database and collection
        mock_collection = Mock()
        mock_mongo_client.__getitem__.return_value.sessions = mock_collection

        # Mock insert result
        mock_result = Mock()
        mock_result.inserted_id = "test-session-id"
        mock_collection.insert_one.return_value = mock_result

        # Create session model
        session = SessionModel(
            id="test-session-id",
            language=LanguageCode.CHINESE,
            status=SessionStatus.ACTIVE,
        )

        result = save_session(session)

        assert result == "test-session-id"
        mock_collection.insert_one.assert_called_once()

    def test_save_session_database_error(self, mock_mongo_client):
        """Test session save with database error."""
        mock_collection = Mock()
        mock_mongo_client.__getitem__.return_value.sessions = mock_collection
        mock_collection.insert_one.side_effect = PyMongoError("Database error")

        session = SessionModel(id="test-session-id", language=LanguageCode.CHINESE)

        with pytest.raises(Exception):  # Should raise DatabaseError
            save_session(session)

    def test_get_session_success(self, mock_mongo_client):
        """Test successful session retrieval."""
        mock_collection = Mock()
        mock_mongo_client.__getitem__.return_value.sessions = mock_collection

        # Mock session document
        mock_session = {
            "_id": "test-session-id",
            "language": "zh",
            "status": "active",
            "created_at": "2025-12-12T15:45:31Z",
        }
        mock_collection.find_one.return_value = mock_session

        result = get_session("test-session-id")

        assert result is not None
        assert result["_id"] == "test-session-id"
        assert result["language"] == "zh"
        assert result["status"] == "active"

    def test_get_session_not_found(self, mock_mongo_client):
        """Test session retrieval when not found."""
        mock_collection = Mock()
        mock_mongo_client.__getitem__.return_value.sessions = mock_collection
        mock_collection.find_one.return_value = None

        result = get_session("non-existent-id")

        assert result is None

    def test_update_session_status_success(self, mock_mongo_client):
        """Test successful session status update."""
        mock_collection = Mock()
        mock_mongo_client.__getitem__.return_value.sessions = mock_collection

        # Mock update result
        mock_result = Mock()
        mock_result.modified_count = 1
        mock_collection.update_one.return_value = mock_result

        result = update_session_status("test-session-id", "closed")

        assert result is True
        mock_collection.update_one.assert_called_once()

    def test_save_transcription_success(self, mock_mongo_client):
        """Test successful transcription save."""
        mock_collection = Mock()
        mock_mongo_client.__getitem__.return_value.transcriptions = mock_collection

        mock_result = Mock()
        mock_result.inserted_id = "test-transcription-id"
        mock_collection.insert_one.return_value = mock_result

        transcription = TranscriptionModel(
            id="test-transcription-id",
            session_id="test-session-id",
            transcript="Hello world",
        )

        result = save_transcription(transcription)

        assert result == "test-transcription-id"
        mock_collection.insert_one.assert_called_once()

    def test_get_transcriptions_by_session_success(self, mock_mongo_client):
        """Test successful transcriptions retrieval."""
        mock_collection = Mock()
        mock_mongo_client.__getitem__.return_value.transcriptions = mock_collection

        # Mock cursor
        mock_cursor = Mock()
        mock_cursor.__iter__ = Mock(
            return_value=iter(
                [
                    {"_id": "test-id-1", "transcript": "Hello"},
                    {"_id": "test-id-2", "transcript": "World"},
                ]
            )
        )
        mock_collection.find.return_value.sort.return_value.limit.return_value = (
            mock_cursor
        )

        result = get_transcriptions_by_session("test-session-id", limit=2)

        assert len(result) == 2
        assert result[0]["transcript"] == "Hello"
        assert result[1]["transcript"] == "World"

    def test_get_latest_transcription_success(self, mock_mongo_client):
        """Test successful latest transcription retrieval."""
        mock_collection = Mock()
        mock_mongo_client.__getitem__.return_value.transcriptions = mock_collection

        mock_cursor = Mock()
        mock_cursor.__iter__ = Mock(
            return_value=iter(
                [{"_id": "test-id", "transcript": "Latest transcription"}]
            )
        )
        mock_collection.find.return_value.sort.return_value.limit.return_value = (
            mock_cursor
        )

        result = get_latest_transcription("test-session-id")

        assert result is not None
        assert result["transcript"] == "Latest transcription"

    def test_get_latest_transcription_empty(self, mock_mongo_client):
        """Test latest transcription retrieval when empty."""
        mock_collection = Mock()
        mock_mongo_client.__getitem__.return_value.transcriptions = mock_collection

        mock_cursor = Mock()
        mock_cursor.__iter__ = Mock(return_value=iter([]))
        mock_collection.find.return_value.sort.return_value.limit.return_value = (
            mock_cursor
        )

        result = get_latest_transcription("test-session-id")

        assert result is None

    def test_save_translation_success(self, mock_mongo_client):
        """Test successful translation save."""
        mock_collection = Mock()
        mock_mongo_client.__getitem__.return_value.translations = mock_collection

        mock_result = Mock()
        mock_result.inserted_id = "test-translation-id"
        mock_collection.insert_one.return_value = mock_result

        translation = TranslationModel(
            id="test-translation-id",
            transcription_id="test-transcription-id",
            transcript="Hello world",
            translation="你好世界",
            language=LanguageCode.CHINESE,
        )

        result = save_translation(translation)

        assert result == "test-translation-id"
        mock_collection.insert_one.assert_called_once()

    def test_get_translations_by_transcription_success(self, mock_mongo_client):
        """Test successful translations retrieval by transcription."""
        mock_collection = Mock()
        mock_mongo_client.__getitem__.return_value.translations = mock_collection

        mock_cursor = Mock()
        mock_cursor.__iter__ = Mock(
            return_value=iter(
                [
                    {"_id": "test-id-1", "translation": "Translation 1"},
                    {"_id": "test-id-2", "translation": "Translation 2"},
                ]
            )
        )
        mock_collection.find.return_value.sort.return_value.limit.return_value = (
            mock_cursor
        )

        result = get_translations_by_transcription("test-transcription-id", limit=2)

        assert len(result) == 2
        assert result[0]["translation"] == "Translation 1"
        assert result[1]["translation"] == "Translation 2"
