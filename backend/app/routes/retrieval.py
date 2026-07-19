import time
import logging
from flask import Blueprint, request, jsonify
from app.services.semantic_retrieval import SemanticRetrievalService, SemanticRetrievalError
from app.services.bm25_retriever import BM25RetrievalService
from app.services.hybrid_retriever import HybridRetrievalService
from app.services.cross_encoder import CrossEncoderService

logger = logging.getLogger("rag_backend.routes.retrieval")

retrieval_bp = Blueprint("retrieval", __name__)

@retrieval_bp.route("/retrieval/search", methods=["POST"])
def search_semantic():
    """
    POST endpoint that accepts a query string and an optional top_k parameter.
    Performs semantic nearest-neighbor retrieval on the vector index and
    returns a ranked list of relevant text chunks.
    """
    data = request.get_json(silent=True) or {}
    query = data.get("query")
    top_k = data.get("top_k")

    if query is None:
        return jsonify({
            "success": False,
            "message": "Missing 'query' parameter in request body."
        }), 400

    start_time = time.time()
    try:
        service = SemanticRetrievalService()
        raw_results = service.search(query, top_k=top_k)
        results = [r.to_dict() for r in raw_results]
        elapsed_time = time.time() - start_time
        
        # Determine actual top_k used (if query is empty, results is empty, so we use top_k from request or default)
        actual_top_k = top_k if isinstance(top_k, int) and top_k > 0 else service._get_default_top_k()

        return jsonify({
            "success": True,
            "query": query,
            "top_k": actual_top_k,
            "retrieval_time_seconds": elapsed_time,
            "results": results
        }), 200
        
    except SemanticRetrievalError as e:
        logger.warning(f"Semantic retrieval request failed: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400
    except Exception as e:
        logger.exception("Unexpected error in semantic retrieval endpoint")
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500

@retrieval_bp.route("/retrieval/bm25", methods=["POST"])
def search_bm25():
    """
    POST endpoint that accepts a query string and an optional top_k parameter.
    Performs sparse BM25 retrieval on document chunks and
    returns a ranked list of relevant text chunks.
    """
    data = request.get_json(silent=True) or {}
    query = data.get("query")
    top_k = data.get("top_k")

    if query is None:
        return jsonify({
            "success": False,
            "message": "Missing 'query' parameter in request body."
        }), 400

    start_time = time.time()
    try:
        service = BM25RetrievalService()
        raw_results = service.search(query, top_k=top_k)
        results = [r.to_dict() for r in raw_results]
        elapsed_time = time.time() - start_time
        
        # Determine actual top_k used
        actual_top_k = top_k if isinstance(top_k, int) and top_k > 0 else service._get_default_top_k()

        return jsonify({
            "success": True,
            "query": query,
            "top_k": actual_top_k,
            "retrieval_time_seconds": elapsed_time,
            "results": results
        }), 200
        
    except Exception as e:
        logger.exception("Unexpected error in BM25 retrieval endpoint")
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500

@retrieval_bp.route("/retrieval/hybrid", methods=["POST"])
def search_hybrid():
    """
    POST endpoint that accepts a query string and an optional top_k parameter.
    Performs reciprocal rank fusion hybrid search over semantic and BM25 systems,
    and returns a ranked list of relevant text chunks.
    """
    data = request.get_json(silent=True) or {}
    query = data.get("query")
    top_k = data.get("top_k")

    if query is None:
        return jsonify({
            "success": False,
            "message": "Missing 'query' parameter in request body."
        }), 400

    start_time = time.time()
    try:
        service = HybridRetrievalService()
        raw_results = service.search(query, top_k=top_k)
        results = [r.to_dict() for r in raw_results]
        elapsed_time = time.time() - start_time
        
        # Determine actual top_k used
        actual_top_k = top_k if isinstance(top_k, int) and top_k > 0 else service._get_default_top_k()

        return jsonify({
            "success": True,
            "query": query,
            "top_k": actual_top_k,
            "retrieval_time_seconds": elapsed_time,
            "results": results
        }), 200
        
    except Exception as e:
        logger.exception("Unexpected error in hybrid retrieval endpoint")
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500

@retrieval_bp.route("/retrieval/rerank", methods=["POST"])
def search_rerank():
    """
    POST endpoint that accepts a query string and an optional top_k parameter.
    Runs a pipeline of Hybrid Retrieval followed by Cross-Encoder reranking.
    Returns a ranked list of relevant text chunks containing rerank_scores.
    """
    data = request.get_json(silent=True) or {}
    query = data.get("query")
    top_k = data.get("top_k")

    if query is None:
        return jsonify({
            "success": False,
            "message": "Missing 'query' parameter in request body."
        }), 400

    start_total = time.time()
    try:
        rerank_service = CrossEncoderService()
        hybrid_service = HybridRetrievalService()

        # Resolve top_k to request
        actual_top_k = top_k if isinstance(top_k, int) and top_k > 0 else rerank_service._get_default_top_k()

        # Retrieve a candidate pool (fetch larger pool of max(top_k * 3, 25) to allow effective reranking)
        candidate_top_k = max(actual_top_k * 3, 25)

        # 1. Run hybrid retrieval
        start_hybrid = time.time()
        hybrid_candidates = hybrid_service.search(query, top_k=candidate_top_k)
        hybrid_latency = time.time() - start_hybrid

        # 2. Run Cross-Encoder reranking
        start_rerank = time.time()
        reranked_results = rerank_service.rerank(query, hybrid_candidates, top_k=actual_top_k)
        rerank_latency = time.time() - start_rerank

        results = [r.to_dict() for r in reranked_results]
        total_latency = time.time() - start_total

        logger.info(
            f"Reranking pipeline completed in {total_latency:.4f}s. "
            f"Pipeline latency: hybrid_retrieval={hybrid_latency:.4f}s, "
            f"cross_encoder_rerank={rerank_latency:.4f}s. "
            f"Query length: {len(query)}, Top-K: {actual_top_k}, candidates evaluated: {len(hybrid_candidates)}."
        )

        return jsonify({
            "success": True,
            "query": query,
            "top_k": actual_top_k,
            "retrieval_time_seconds": total_latency,
            "hybrid_retrieval_time_seconds": hybrid_latency,
            "rerank_time_seconds": rerank_latency,
            "results": results
        }), 200

    except Exception as e:
        logger.exception("Unexpected error in rerank retrieval endpoint")
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500
