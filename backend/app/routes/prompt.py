import time
import logging
from flask import Blueprint, request, jsonify
from app.services.hybrid_retriever import HybridRetrievalService
from app.services.cross_encoder import CrossEncoderService
from app.services.prompt_builder import (
    PromptBuilderService,
    PromptBuilderError,
    PromptValidationError
)

logger = logging.getLogger("rag_backend.routes.prompt")

prompt_bp = Blueprint("prompt", __name__)

@prompt_bp.route("/prompt/build", methods=["POST"])
def build_prompt_endpoint():
    """
    POST endpoint executing the production RAG preparation pipeline:
      User Query -> Hybrid Retrieval -> Cross-Encoder Reranking -> Prompt Builder -> Return Prompt.

    Accepts custom pre-reranked result payloads directly via 'results' to bypass retrieval if needed.

    Returns structured JSON with prompt text, line count, character count, token estimate, SHA-256 hash,
    versioning tags, and validation metrics. Does NOT invoke external LLM APIs.
    """
    data = request.get_json(silent=True) or {}
    query = data.get("query")
    top_k = data.get("top_k")
    template_version = data.get("template_version")
    max_chunks = data.get("max_chunks")
    max_chars = data.get("max_chars")
    provided_results = data.get("results")

    if query is None:
        return jsonify({
            "success": False,
            "message": "Missing 'query' parameter in request body."
        }), 400

    start_pipeline = time.time()
    try:
        prompt_service = PromptBuilderService()

        if provided_results is not None:
            # Direct build from provided retrieval results
            logger.info("Building prompt from directly provided retrieval results payload.")
            reranked_results = provided_results
            pipeline_latency = 0.0
        else:
            # Full RAG Pipeline: Hybrid Retrieval -> Cross Encoder Rerank -> Prompt Builder
            hybrid_service = HybridRetrievalService()
            rerank_service = CrossEncoderService()

            actual_top_k = top_k if (isinstance(top_k, int) and top_k > 0) else rerank_service._get_default_top_k()
            candidate_top_k = max(actual_top_k * 3, 25)

            # Step 1: Hybrid Retrieval
            candidates = hybrid_service.search(query, top_k=candidate_top_k)

            # Step 2: Cross-Encoder Reranking
            reranked_results = rerank_service.rerank(query, candidates, top_k=actual_top_k)
            pipeline_latency = time.time() - start_pipeline

        # Step 3: Build Prompt
        prompt_result = prompt_service.build_prompt(
            query=query,
            retrieval_results=reranked_results,
            template_version=template_version,
            max_chunks=max_chunks,
            max_chars=max_chars
        )

        total_latency = time.time() - start_pipeline

        return jsonify({
            "success": True,
            "query": prompt_result["query"],
            "prompt": prompt_result["prompt"],
            "prompt_length": prompt_result["prompt_length"],
            "character_count": prompt_result["character_count"],
            "context_chunk_count": prompt_result["context_chunk_count"],
            "estimated_tokens": prompt_result["estimated_tokens"],
            "template_version": prompt_result["template_version"],
            "prompt_version": prompt_result["prompt_version"],
            "pipeline_version": prompt_result["pipeline_version"],
            "prompt_hash": prompt_result["prompt_hash"],
            "generation_time_seconds": prompt_result["generation_time_seconds"],
            "pipeline_time_seconds": total_latency,
            "truncated": prompt_result["truncated"],
            "validation": prompt_result["validation"],
            "results": prompt_result["results"]
        }), 200

    except PromptValidationError as e:
        logger.warning(f"Prompt validation failed: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400
    except PromptBuilderError as e:
        logger.warning(f"Prompt builder request failed: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400
    except Exception as e:
        logger.exception("Unexpected error in prompt build endpoint")
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500
