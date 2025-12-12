"""Server-Sent Events for real-time updates."""

import json
import time
from flask import Blueprint, Response, request, current_app
from app.models.schemas import APIResponse
from app.services.database import get_latest_transcription, get_translations_by_session

sse_bp = Blueprint("sse", __name__, url_prefix="/api/sse")


@sse_bp.route("/translation/<session_id>", methods=["GET"])
def translation_stream(session_id):
    """Stream real-time translation updates for a session.

    Args:
        session_id: Session ID to stream translations for.

    Returns:
        SSE stream with translation updates.
    """

    def generate():
        # Track the last known translation to avoid duplicates
        last_translation_id = None

        # Send initial connection message
        yield f"data: {json.dumps({'type': 'connected', 'session_id': session_id})}\n\n"

        with current_app.app_context():
            while True:
                try:
                    # Get latest transcription
                    transcription = get_latest_transcription(session_id)

                    if transcription:
                        # Get latest translation for this transcription
                        translations = get_translations_by_session(session_id, limit=1)

                        if translations:
                            latest_translation = translations[-1]
                            translation_id = latest_translation.get("_id")

                            # Only send if we have a new translation
                            if translation_id != last_translation_id:
                                last_translation_id = translation_id

                                # Send translation update
                                update_data = {
                                    "type": "translation",
                                    "session_id": session_id,
                                    "transcription": transcription,
                                    "translation": latest_translation,
                                    "timestamp": time.time(),
                                }
                                yield f"data: {json.dumps(update_data)}\n\n"

                    # Send heartbeat every 5 seconds
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': time.time()})}\n\n"

                    # Wait before next check
                    time.sleep(2)

                except Exception as e:
                    # Send error message and continue
                    error_data = {
                        "type": "error",
                        "message": str(e),
                        "timestamp": time.time(),
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    time.sleep(5)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        },
    )


@sse_bp.route("/session/<session_id>", methods=["GET"])
def session_stream(session_id):
    """Stream real-time session status updates.

    Args:
        session_id: Session ID to stream status for.

    Returns:
        SSE stream with session status updates.
    """

    def generate():
        from app.services.database import get_session

        # Send initial connection message
        yield f"data: {json.dumps({'type': 'connected', 'session_id': session_id})}\n\n"

        last_status = None

        with current_app.app_context():
            while True:
                try:
                    # Get current session status
                    session = get_session(session_id)

                    if session:
                        current_status = session.get("status")

                        # Only send if status changed
                        if current_status != last_status:
                            last_status = current_status

                            status_data = {
                                "type": "status_change",
                                "session_id": session_id,
                                "status": current_status,
                                "timestamp": time.time(),
                            }
                            yield f"data: {json.dumps(status_data)}\n\n"

                    # Send heartbeat every 10 seconds
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': time.time()})}\n\n"

                    # Wait before next check
                    time.sleep(5)

                except Exception as e:
                    # Send error message and continue
                    error_data = {
                        "type": "error",
                        "message": str(e),
                        "timestamp": time.time(),
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    time.sleep(5)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        },
    )
