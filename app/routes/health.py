"""Health check endpoints."""

from flask import Blueprint, jsonify, current_app

from app.models.schemas import HealthResponse

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """Check application health status.
    
    Returns:
        JSON response with health status of all components.
    """
    mongo_status = _check_mongo()
    ffmpeg_status = _check_ffmpeg()
    
    response = HealthResponse(
        status="healthy" if mongo_status else "degraded",
        mongo_connected=mongo_status,
        ffmpeg_installed=ffmpeg_status,
    )
    
    return jsonify(response.model_dump())


def _check_mongo() -> bool:
    """Check MongoDB connection status."""
    try:
        if current_app.mongo_client:
            current_app.mongo_client.admin.command("ping")
            return True
    except Exception:
        pass
    return False


def _check_ffmpeg() -> bool:
    """Check if FFmpeg is available."""
    try:
        import subprocess
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False
