from flask import Blueprint, jsonify
import sys

health_bp = Blueprint("health", __name__)

@health_bp.route("/health", methods=["GET"])
def health_check():
    """Returns application health status details."""
    return jsonify({
        "status": "healthy",
        "api": "Evidence-Grounded AI Research Assistant API",
        "version": "1.0.0",
        "python_version": sys.version.split()[0],
        "success": True
    }), 200
