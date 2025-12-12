"""Session management endpoints."""

import uuid
from flask import Blueprint, jsonify, request
from datetime import datetime

from app.models.schemas import (
    SessionCreate,
    SessionResponse,
    APIResponse,
    SessionStatus,
    LanguageCode,
    SessionModel,
)
from app.services.database import save_session, get_session, update_session_status

session_bp = Blueprint("session", __name__, url_prefix="/api/session")


@session_bp.route("", methods=["POST"])
def create_session():
    """Create a new translation session.

    Returns:
        JSON response with session details.
    """
    try:
        # Parse request data
        data = request.get_json() or {}
        session_create = SessionCreate(**data)

        # Create session model
        session_id = str(uuid.uuid4())
        session_model = SessionModel(
            id=session_id, language=session_create.language, status=SessionStatus.ACTIVE
        )

        # Save to database
        saved_id = save_session(session_model)

        # Create response
        response = SessionResponse(
            id=saved_id,
            language=session_create.language,
            status=SessionStatus.ACTIVE,
            created_at=datetime.utcnow(),
        )

        return jsonify(
            APIResponse(
                success=True,
                message="Session created successfully",
                data=response.model_dump(),
            ).model_dump()
        ), 201

    except Exception as e:
        return jsonify(
            APIResponse(
                success=False, message=f"Failed to create session: {str(e)}", data=None
            ).model_dump()
        ), 400


@session_bp.route("/<session_id>/status", methods=["GET"])
def get_session_status(session_id):
    """Get session status.

    Args:
        session_id: Session ID to check.

    Returns:
        JSON response with session status.
    """
    try:
        session = get_session(session_id)

        if not session:
            return jsonify(
                APIResponse(
                    success=False, message="Session not found", data=None
                ).model_dump()
            ), 404

        return jsonify(
            APIResponse(
                success=True,
                message="Session status retrieved",
                data={
                    "session_id": session_id,
                    "status": session["status"],
                    "language": session["language"],
                    "created_at": session["created_at"],
                },
            ).model_dump()
        )

    except Exception as e:
        return jsonify(
            APIResponse(
                success=False,
                message=f"Failed to get session status: {str(e)}",
                data=None,
            ).model_dump()
        ), 500


@session_bp.route("/<session_id>", methods=["DELETE"])
def close_session(session_id):
    """Close a translation session.

    Args:
        session_id: Session ID to close.

    Returns:
        JSON response confirming session closure.
    """
    try:
        success = update_session_status(session_id, SessionStatus.CLOSED)

        if not success:
            return jsonify(
                APIResponse(
                    success=False,
                    message="Session not found or already closed",
                    data=None,
                ).model_dump()
            ), 404

        return jsonify(
            APIResponse(
                success=True,
                message="Session closed successfully",
                data={"session_id": session_id, "status": SessionStatus.CLOSED},
            ).model_dump()
        )

    except Exception as e:
        return jsonify(
            APIResponse(
                success=False, message=f"Failed to close session: {str(e)}", data=None
            ).model_dump()
        ), 500
