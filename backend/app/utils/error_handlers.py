from flask import jsonify
import logging

logger = logging.getLogger("rag_backend.error_handler")

class APIException(Exception):
    """Base API exception class for predictable errors."""
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        rv["success"] = False
        return rv

def register_error_handlers(app):
    """Registers standard HTTP and custom API error handlers with the Flask app."""
    
    @app.errorhandler(APIException)
    def handle_api_exception(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        logger.warning(f"APIException: {error.message} (status: {error.status_code})")
        return response

    @app.errorhandler(400)
    def handle_bad_request(error):
        response = jsonify({
            "success": False,
            "message": str(error.description or "Bad request syntax or unsupported method"),
            "error_type": "BadRequest"
        })
        response.status_code = 400
        return response

    @app.errorhandler(404)
    def handle_not_found(error):
        response = jsonify({
            "success": False,
            "message": "Resource not found on this server",
            "error_type": "NotFound"
        })
        response.status_code = 404
        return response

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        response = jsonify({
            "success": False,
            "message": "The method is not allowed for the requested URL.",
            "error_type": "MethodNotAllowed"
        })
        response.status_code = 405
        return response

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logger.exception("An unhandled exception occurred in the application")
        response = jsonify({
            "success": False,
            "message": "An unexpected error occurred on the server",
            "error_type": "InternalServerError"
        })
        response.status_code = 500
        return response
