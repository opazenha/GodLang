from flask import Blueprint, jsonify, current_app
from pydantic import BaseModel
import ffmpeg

bp = Blueprint('main', __name__)

class HealthResponse(BaseModel):
    status: str
    mongo_connected: bool
    ffmpeg_installed: bool

@bp.route('/health', methods=['GET'])
def health_check():
    mongo_status = False
    try:
        current_app.mongo_client.admin.command('ping')
        mongo_status = True
    except Exception:
        mongo_status = False

    # Assume ffmpeg is available if the import succeeded
    ffmpeg_status = True

    return jsonify(HealthResponse(
        status="active",
        mongo_connected=mongo_status,
        ffmpeg_installed=ffmpeg_status
    ).model_dump())
