import time
import logging
from flask import Blueprint, request, jsonify
from app.services.query_embedding import QueryEmbeddingService, QueryEmbeddingError

logger = logging.getLogger("rag_backend.routes.query")

query_bp = Blueprint("query", __name__)

@query_bp.route("/query/embed", methods=["POST"])
def embed_query():
    """
    POST endpoint that accepts a query string, generates a normalized embedding,
    and returns only metadata (e.g. dimensions, processing time).
    Does not return the actual vector embedding to the client.
    """
    data = request.get_json(silent=True) or {}
    query = data.get("query")

    if query is None:
        return jsonify({
            "success": False,
            "message": "Missing 'query' parameter in request body."
        }), 400

    start_time = time.time()
    try:
        service = QueryEmbeddingService()
        embedding = service.generate_query_embedding(query)
        elapsed_time = time.time() - start_time
        
        return jsonify({
            "success": True,
            "query_length": len(query.strip()),
            "embedding_dimension": len(embedding),
            "processing_time_seconds": elapsed_time,
            "message": "Successfully generated query embedding."
        }), 200
        
    except QueryEmbeddingError as e:
        logger.warning(f"Query embedding validation or processing failed: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400
    except Exception as e:
        logger.exception("Unexpected error in query embed endpoint")
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500
