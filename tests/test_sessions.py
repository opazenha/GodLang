"""Unit tests for session endpoints."""

import json
import pytest
from unittest.mock import patch, Mock

from app.models.schemas import SessionStatus


class TestSessionEndpoints:
    """Test session management endpoints."""

    def test_create_session_success(
        self, client, sample_session_data, mock_mongo_client
    ):
        """Test successful session creation."""
        # Mock database operations
        mock_mongo_client.__getitem__.return_value.sessions.insert_one.return_value.inserted_id = "test-session-id"

        response = client.post(
            "/api/session",
            data=json.dumps(sample_session_data),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["message"] == "Session created successfully"
        assert "data" in data
        assert data["data"]["language"] == "zh"
        assert data["data"]["status"] == "active"

    def test_create_session_invalid_data(self, client):
        """Test session creation with invalid data."""
        invalid_data = {"language": "invalid"}

        response = client.post(
            "/api/session",
            data=json.dumps(invalid_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "Failed to create session" in data["message"]

    def test_get_session_status_success(self, client, mock_mongo_client):
        """Test successful session status retrieval."""
        # Mock session data
        mock_session = {
            "_id": "test-session-id",
            "status": "active",
            "language": "zh",
            "created_at": "2025-12-12T15:45:31Z",
        }
        mock_mongo_client.__getitem__.return_value.sessions.find_one.return_value = (
            mock_session
        )

        response = client.get("/api/session/test-session-id/status")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["session_id"] == "test-session-id"
        assert data["data"]["status"] == "active"
        assert data["data"]["language"] == "zh"

    def test_get_session_status_not_found(self, client, mock_mongo_client):
        """Test session status for non-existent session."""
        mock_mongo_client.__getitem__.return_value.sessions.find_one.return_value = None

        response = client.get("/api/session/non-existent-session/status")

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["message"] == "Session not found"

    def test_close_session_success(self, client, mock_mongo_client):
        """Test successful session closure."""
        # Mock update result
        mock_mongo_client.__getitem__.return_value.sessions.update_one.return_value.modified_count = 1

        response = client.delete("/api/session/test-session-id")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["message"] == "Session closed successfully"
        assert data["data"]["session_id"] == "test-session-id"
        assert data["data"]["status"] == "closed"

    def test_close_session_not_found(self, client, mock_mongo_client):
        """Test closing non-existent session."""
        mock_mongo_client.__getitem__.return_value.sessions.update_one.return_value.modified_count = 0

        response = client.delete("/api/session/non-existent-session")

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data["success"] is False
        assert "not found or already closed" in data["message"]
