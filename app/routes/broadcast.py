"""Broadcast management endpoints for live transcription sessions."""

from flask import Blueprint, jsonify, request

from app.models.schemas import APIResponse, LanguageCode
from app.services.broadcast import get_broadcast_manager, BroadcastStatus

broadcast_bp = Blueprint("broadcast", __name__, url_prefix="/api/broadcast")


@broadcast_bp.route("/status", methods=["GET"])
def get_status():
    """Get broadcast status for all languages or a specific language.
    
    Query Parameters:
        language: Optional language code (e.g., 'zh' for Chinese).
        
    Returns:
        JSON response with broadcast status.
    """
    try:
        manager = get_broadcast_manager()
        language_param = request.args.get("language")
        
        if language_param:
            try:
                language = LanguageCode(language_param)
            except ValueError:
                return jsonify(
                    APIResponse(
                        success=False,
                        message=f"Invalid language code: {language_param}",
                        data=None,
                    ).model_dump()
                ), 400
            
            status = manager.get_status(language)
        else:
            status = manager.get_status()
        
        return jsonify(
            APIResponse(
                success=True,
                message="Broadcast status retrieved",
                data=status,
            ).model_dump()
        )
        
    except Exception as e:
        return jsonify(
            APIResponse(
                success=False,
                message=f"Failed to get status: {str(e)}",
                data=None,
            ).model_dump()
        ), 500


@broadcast_bp.route("/start", methods=["POST"])
def start_broadcast():
    """Start a broadcast session for a language.
    
    Request Body:
        language: Language code (default: 'zh' for Chinese).
        
    Returns:
        JSON response with session details.
    """
    try:
        manager = get_broadcast_manager()
        data = request.get_json() or {}
        
        # Get language, default to Chinese
        language_param = data.get("language", "zh")
        try:
            language = LanguageCode(language_param)
        except ValueError:
            return jsonify(
                APIResponse(
                    success=False,
                    message=f"Invalid language code: {language_param}",
                    data=None,
                ).model_dump()
            ), 400
        
        # Check if already active
        if manager.is_active(language):
            broadcast = manager.get_broadcast(language)
            return jsonify(
                APIResponse(
                    success=True,
                    message="Broadcast already active",
                    data=broadcast.to_dict() if broadcast else None,
                ).model_dump()
            )
        
        # Start new broadcast
        broadcast = manager.start_broadcast(language)
        
        return jsonify(
            APIResponse(
                success=True,
                message="Broadcast started successfully",
                data=broadcast.to_dict(),
            ).model_dump()
        ), 201
        
    except ValueError as e:
        return jsonify(
            APIResponse(
                success=False,
                message=str(e),
                data=None,
            ).model_dump()
        ), 409
        
    except Exception as e:
        return jsonify(
            APIResponse(
                success=False,
                message=f"Failed to start broadcast: {str(e)}",
                data=None,
            ).model_dump()
        ), 500


@broadcast_bp.route("/stop", methods=["POST"])
def stop_broadcast():
    """Stop a broadcast session for a language.
    
    Request Body:
        language: Language code (default: 'zh' for Chinese).
        
    Returns:
        JSON response confirming stop.
    """
    try:
        manager = get_broadcast_manager()
        data = request.get_json() or {}
        
        # Get language, default to Chinese
        language_param = data.get("language", "zh")
        try:
            language = LanguageCode(language_param)
        except ValueError:
            return jsonify(
                APIResponse(
                    success=False,
                    message=f"Invalid language code: {language_param}",
                    data=None,
                ).model_dump()
            ), 400
        
        # Stop broadcast
        stopped = manager.stop_broadcast(language)
        
        if not stopped:
            return jsonify(
                APIResponse(
                    success=False,
                    message=f"No active broadcast for {language.value}",
                    data=None,
                ).model_dump()
            ), 404
        
        return jsonify(
            APIResponse(
                success=True,
                message="Broadcast stopped successfully",
                data={"language": language.value},
            ).model_dump()
        )
        
    except Exception as e:
        return jsonify(
            APIResponse(
                success=False,
                message=f"Failed to stop broadcast: {str(e)}",
                data=None,
            ).model_dump()
        ), 500
