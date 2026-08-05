import logging
from typing import Tuple, Any, Dict
from flask import Blueprint, request, jsonify, Response

from app.services.session_service import (
    create_session,
    list_sessions,
    get_session,
    rename_session,
    delete_session,
    load_session_history
)

logger = logging.getLogger("rag_backend.routes.session_routes")

session_bp = Blueprint("session_routes", __name__)

def extract_user_info() -> Dict[str, Any]:
    """Extracts optional authenticated user headers from request."""
    return {
        "firebase_uid": request.headers.get("X-User-UID") or request.args.get("firebase_uid"),
        "email": request.headers.get("X-User-Email") or request.args.get("email")
    }

@session_bp.route("/sessions", methods=["POST"])
def api_create_session() -> Tuple[Any, int]:
    """
    POST /api/sessions
    Creates a new persistent research session in PostgreSQL.
    """
    try:
        data = request.get_json(silent=True) or {}
        title = data.get("title")
        user_info = extract_user_info()

        session = create_session(user_info=user_info, title=title)
        return jsonify({
            "success": True,
            "message": "Research session created successfully.",
            "session": session.to_dict()
        }), 201
    except Exception as e:
        logger.exception("Failed to create research session")
        return jsonify({
            "success": False,
            "message": f"Failed to create session: {str(e)}"
        }), 500

@session_bp.route("/sessions", methods=["GET"])
def api_list_sessions() -> Tuple[Any, int]:
    """
    GET /api/sessions
    Lists all persistent research sessions sorted by latest activity (updated_at DESC).
    """
    try:
        user_info = extract_user_info()
        sessions = list_sessions(user_info=user_info)
        serialized = [s.to_dict() for s in sessions]

        return jsonify({
            "success": True,
            "count": len(serialized),
            "sessions": serialized
        }), 200
    except Exception as e:
        logger.exception("Failed to list research sessions")
        return jsonify({
            "success": False,
            "message": f"Failed to list sessions: {str(e)}"
        }), 500

@session_bp.route("/sessions/<session_id>", methods=["GET"])
def api_get_session_history(session_id: str) -> Tuple[Any, int]:
    """
    GET /api/sessions/<session_id>
    Loads full conversation history and chunk attribution logs for a specific research session.
    """
    try:
        session_data = load_session_history(session_id)
        return jsonify({
            "success": True,
            "session": session_data
        }), 200
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 404
    except Exception as e:
        logger.exception(f"Failed to load history for session {session_id}")
        return jsonify({
            "success": False,
            "message": f"Failed to load session history: {str(e)}"
        }), 500

@session_bp.route("/sessions/<session_id>", methods=["PATCH"])
def api_rename_session(session_id: str) -> Tuple[Any, int]:
    """
    PATCH /api/sessions/<session_id>
    Renames a research session title in PostgreSQL.
    """
    try:
        data = request.get_json(silent=True) or {}
        new_title = data.get("title") or data.get("filename")
        if not new_title or not str(new_title).strip():
            return jsonify({
                "success": False,
                "message": "Title cannot be empty."
            }), 400

        session = rename_session(session_id, str(new_title).strip())
        return jsonify({
            "success": True,
            "message": "Research session renamed successfully.",
            "session": session.to_dict()
        }), 200
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 404
    except Exception as e:
        logger.exception(f"Failed to rename session {session_id}")
        return jsonify({
            "success": False,
            "message": f"Failed to rename session: {str(e)}"
        }), 500

@session_bp.route("/sessions/<session_id>", methods=["DELETE"])
def api_delete_session(session_id: str) -> Tuple[Any, int]:
    """
    DELETE /api/sessions/<session_id>
    Deletes a research session from PostgreSQL, cascade-deleting all messages and retrieval logs.
    """
    try:
        deleted = delete_session(session_id)
        if not deleted:
            return jsonify({
                "success": False,
                "message": f"Research session '{session_id}' not found."
            }), 404

        return jsonify({
            "success": True,
            "session_id": session_id,
            "message": "Research session deleted successfully."
        }), 200
    except Exception as e:
        logger.exception(f"Failed to delete session {session_id}")
        return jsonify({
            "success": False,
            "message": f"Failed to delete session: {str(e)}"
        }), 500

@session_bp.route("/sessions/<session_id>/export", methods=["GET"])
def api_export_session(session_id: str) -> Tuple[Any, int]:
    """
    GET /api/sessions/<session_id>/export?format=markdown|json|pdf
    Exports a full research transcript in Markdown, JSON, or PDF format.
    """
    export_format = request.args.get("format", default="markdown").lower()
    try:
        from app.services.export_service import export_session_content
        content, mime_type, filename = export_session_content(session_id, export_format)

        return Response(
            content,
            mimetype=mime_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        ), 200
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 404
    except Exception as e:
        logger.exception(f"Failed to export session {session_id}")
        return jsonify({
            "success": False,
            "message": f"Session export failed: {str(e)}"
        }), 500
