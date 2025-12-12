"""Unit tests for health endpoint."""

import json
import pytest
from unittest.mock import patch, Mock


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check_healthy(self, client):
        """Test health check when all components are healthy."""
        with (
            patch("app.routes.health._check_mongo", return_value=True),
            patch("app.routes.health._check_ffmpeg", return_value=True),
        ):
            response = client.get("/health")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["status"] == "healthy"
            assert data["mongo_connected"] is True
            assert data["ffmpeg_installed"] is True

    def test_health_check_degraded_mongo(self, client):
        """Test health check when MongoDB is down."""
        with (
            patch("app.routes.health._check_mongo", return_value=False),
            patch("app.routes.health._check_ffmpeg", return_value=True),
        ):
            response = client.get("/health")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["status"] == "degraded"
            assert data["mongo_connected"] is False
            assert data["ffmpeg_installed"] is True

    def test_health_check_degraded_ffmpeg(self, client):
        """Test health check when FFmpeg is not available."""
        with (
            patch("app.routes.health._check_mongo", return_value=True),
            patch("app.routes.health._check_ffmpeg", return_value=False),
        ):
            response = client.get("/health")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["status"] == "degraded"
            assert data["mongo_connected"] is True
            assert data["ffmpeg_installed"] is False

    def test_check_mongo_success(self):
        """Test MongoDB connection check success."""
        from app.routes.health import _check_mongo

        with patch("flask.current_app") as mock_app:
            mock_client = Mock()
            mock_app.mongo_client = mock_client
            mock_client.admin.command.return_value = {"ok": 1}

            result = _check_mongo()
            assert result is True

    def test_check_mongo_failure(self):
        """Test MongoDB connection check failure."""
        from app.routes.health import _check_mongo

        with patch("flask.current_app") as mock_app:
            mock_app.mongo_client = None

            result = _check_mongo()
            assert result is False

    def test_check_ffmpeg_success(self):
        """Test FFmpeg availability check success."""
        from app.routes.health import _check_ffmpeg

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            result = _check_ffmpeg()
            assert result is True

    def test_check_ffmpeg_failure(self):
        """Test FFmpeg availability check failure."""
        from app.routes.health import _check_ffmpeg

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("FFmpeg not found")

            result = _check_ffmpeg()
            assert result is False
