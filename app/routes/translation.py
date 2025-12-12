"""Translation endpoints."""

from flask import Blueprint, jsonify, request

from app.models.schemas import APIResponse
from app.services.database import get_latest_transcription, get_translations_by_session

translation_bp = Blueprint("translation", __name__, url_prefix="/api/translation")


@translation_bp.route("/<session_id>", methods=["GET"])
def get_translation(session_id):
    """Get latest translation for a session.

    Args:
        session_id: Session ID to get translation for.

    Returns:
        JSON response with latest translation or message if none found.
    """
    try:
        # Get latest transcription first
        transcription = get_latest_transcription(session_id)

        if not transcription:
            return jsonify(
                APIResponse(
                    success=True,
                    message="No transcriptions found for this session",
                    data=None,
                ).model_dump()
            )

        # Get translations for this transcription
        translations = get_translations_by_session(session_id, limit=1)

        if not translations:
            return jsonify(
                APIResponse(
                    success=True,
                    message="No translations found yet",
                    data={"transcription": transcription, "translation": None},
                ).model_dump()
            )

        # Return the latest translation
        latest_translation = translations[-1]  # Get most recent

        return jsonify(
            APIResponse(
                success=True,
                message="Translation retrieved successfully",
                data={
                    "transcription": transcription,
                    "translation": latest_translation,
                },
            ).model_dump()
        )

    except Exception as e:
        return jsonify(
            APIResponse(
                success=False, message=f"Failed to get translation: {str(e)}", data=None
            ).model_dump()
        ), 500


@translation_bp.route("/<session_id>/all", methods=["GET"])
def get_all_translations(session_id):
    """Get all translations for a session.

    Args:
        session_id: Session ID to get translations for.

    Query Parameters:
        limit: Optional maximum number of results to return.

    Returns:
        JSON response with all translations for the session.
    """
    try:
        # Get limit from query params
        limit = request.args.get("limit", type=int)

        # Get all translations for the session
        translations = get_translations_by_session(session_id, limit=limit)

        return jsonify(
            APIResponse(
                success=True,
                message=f"Retrieved {len(translations)} translations",
                data={
                    "session_id": session_id,
                    "translations": translations,
                    "count": len(translations),
                },
            ).model_dump()
        )

    except Exception as e:
        return jsonify(
            APIResponse(
                success=False,
                message=f"Failed to get translations: {str(e)}",
                data=None,
            ).model_dump()
        ), 500
