import logging
from flask import Blueprint, jsonify, current_app
from sqlalchemy import text
from database import db

logger = logging.getLogger("rag_backend.routes.database")

database_bp = Blueprint("database", __name__)

@database_bp.route("/database/health", methods=["GET"])
def database_health():
    """
    Checks PostgreSQL connection status and returns JSON status response.
    Returns graceful disabled status when running without PostgreSQL.
    """
    if not current_app.config.get("DATABASE_ENABLED", True):
        return jsonify({
            "database": "disabled",
            "status": "running_without_database"
        }), 200

    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({
            "database": "connected"
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.warning(f"PostgreSQL database connection check failed: {e}")
        return jsonify({
            "database": "disconnected",
            "error": str(e)
        }), 503
