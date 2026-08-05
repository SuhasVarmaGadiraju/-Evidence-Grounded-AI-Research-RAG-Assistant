import logging
from typing import Tuple, Any
from flask import Blueprint, request, jsonify
from app.services.user_service import sync_user_profile
from app.utils.error_handlers import APIException

logger = logging.getLogger("rag_backend.routes.auth")

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/users/sync", methods=["POST"])
def sync_user() -> Tuple[Any, int]:
    """
    API Endpoint to synchronize Firebase authenticated user into PostgreSQL.

    Expects JSON payload with:
        - firebase_uid (or id/uid): str
        - email: str
        - name: Optional[str]
        - photo_url: Optional[str]
        - provider: Optional[str]

    Returns:
        JSON response with success status and user record.
    """
    data = request.get_json() or {}
    logger.info(f"Received user profile synchronization request for email: {data.get('email')}")

    try:
        user = sync_user_profile(data)
        return jsonify({
            "success": True,
            "message": "User profile synchronized successfully.",
            "user": user.to_dict()
        }), 200
    except ValueError as ve:
        raise APIException(str(ve), status_code=400)
    except Exception as e:
        logger.exception(f"Unexpected error during user sync route handling: {e}")
        raise APIException(f"Failed to sync user: {str(e)}", status_code=500)
