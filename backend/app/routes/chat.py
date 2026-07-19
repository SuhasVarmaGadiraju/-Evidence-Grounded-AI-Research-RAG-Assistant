import time
import hashlib
import logging
from flask import Blueprint, request, jsonify, current_app
from app.utils.profiler import PipelineProfiler
from app.services.cache_service import llm_cache, retrieval_cache, get_all_cache_stats
from app.services.hybrid_retriever import HybridRetrievalService
from app.services.cross_encoder import CrossEncoderService
from app.services.prompt_builder import PromptBuilderService, PromptBuilderError
from app.services.llm_service import (
    LLMService,
    LLMServiceError,
    LLMAuthenticationError,
    LLMTimeoutError
)

logger = logging.getLogger("rag_backend.routes.chat")

chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/chat/health", methods=["GET"])
def chat_health_endpoint():
    """
    GET endpoint checking local LLM configuration, model readiness, cache stats, and service uptime.
    
    Returns:
        JSON: provider, configured, model, service_status, readiness_checks, cache_stats, uptime_seconds
    """
    try:
        service = LLMService()
        health_info = service.health_check()
        
        # Calculate uptime
        startup_time = current_app.config.get("STARTUP_TIME", time.time())
        uptime_seconds = round(time.time() - startup_time, 2)
        
        # Retrieval Readiness Checks
        try:
            from app.services.embedding import get_embedding_model
            embedding_loaded = get_embedding_model() is not None
        except Exception:
            embedding_loaded = False

        try:
            from app.services.cross_encoder import get_cross_encoder_model
            cross_encoder_loaded = get_cross_encoder_model() is not None
        except Exception:
            cross_encoder_loaded = False

        try:
            from app.services.bm25_index import get_bm25_index_service
            bm25_ready = get_bm25_index_service().is_indexed()
        except Exception:
            bm25_ready = False

        try:
            from app.services.vector_index import get_vector_index_service
            faiss_ready = get_vector_index_service().is_indexed()
        except Exception:
            faiss_ready = False

        prompt_template_loaded = True

        return jsonify({
            "success": True,
            **health_info,
            "readiness": {
                "embedding_loaded": embedding_loaded,
                "cross_encoder_loaded": cross_encoder_loaded,
                "bm25_ready": bm25_ready,
                "faiss_ready": faiss_ready,
                "prompt_template_loaded": prompt_template_loaded,
                "nvidia_api_configured": health_info.get("configured", False)
            },
            "cache_stats": get_all_cache_stats(),
            "uptime_seconds": uptime_seconds
        }), 200
    except Exception as e:
        logger.exception("Error during LLM health check")
        return jsonify({
            "success": False,
            "provider": "NVIDIA",
            "configured": False,
            "service_status": "unhealthy",
            "message": str(e)
        }), 500

@chat_bp.route("/chat", methods=["POST"])
def chat_endpoint():
    """
    POST endpoint executing the optimized end-to-end RAG Generation pipeline:
      User Query → Retrieval Cache → Hybrid Retrieval → Rerank Candidate Pool → Prompt Builder → LLM Cache → NVIDIA API → Grounded Answer
    """
    data = request.get_json(silent=True) or {}
    query = data.get("query")
    top_k = data.get("top_k")
    template_version = data.get("template_version")

    if not query or not str(query).strip():
        return jsonify({
            "success": False,
            "message": "Missing or empty 'query' parameter in request body."
        }), 400

    clean_query = str(query).strip()
    profiler = PipelineProfiler()
    query_hash = hashlib.sha256(clean_query.encode("utf-8")).hexdigest()[:12]

    try:
        rerank_service = CrossEncoderService()
        actual_top_k = top_k if (isinstance(top_k, int) and top_k > 0) else rerank_service._get_default_top_k()

        # Step 1: Check Retrieval Cache
        retrieval_cache_key = f"{clean_query}:{actual_top_k}:{template_version or 'default'}"
        cached_retrieval_payload = None

        if current_app.config.get("CACHE_ENABLED", True):
            cached_retrieval_payload = retrieval_cache.get(retrieval_cache_key)

        if cached_retrieval_payload:
            prompt_result = cached_retrieval_payload["prompt_result"]
            included_chunks = cached_retrieval_payload["included_chunks"]
            profiler.record_stage("retrieval_and_rerank", 0.0001)
        else:
            with profiler.profile("hybrid_retrieval"):
                hybrid_service = HybridRetrievalService()
                # Candidate pool limit optimization: rerank candidate pool size
                candidate_pool_limit = current_app.config.get("RERANK_CANDIDATE_POOL", 20)
                candidate_top_k = max(actual_top_k, candidate_pool_limit)
                candidates = hybrid_service.search(clean_query, top_k=candidate_top_k)

            with profiler.profile("cross_encoder"):
                reranked_results = rerank_service.rerank(clean_query, candidates, top_k=actual_top_k)

            with profiler.profile("prompt_builder"):
                prompt_service = PromptBuilderService()
                prompt_result = prompt_service.build_prompt(
                    query=clean_query,
                    retrieval_results=reranked_results,
                    template_version=template_version
                )

            included_chunks = prompt_result["results"]

            if current_app.config.get("CACHE_ENABLED", True):
                retrieval_cache.set(retrieval_cache_key, {
                    "prompt_result": prompt_result,
                    "included_chunks": included_chunks
                })

        rendered_prompt = prompt_result["prompt"]
        prompt_hash = prompt_result["prompt_hash"]

        # Format inline citations metadata
        citations = []
        for chunk in included_chunks:
            citations.append({
                "document_name": chunk.get("document_name", "Unknown"),
                "page_number": chunk.get("page_number", 0),
                "chunk_id": chunk.get("chunk_id", ""),
                "text": chunk.get("text", "")
            })

        # Step 2: Check LLM Response Cache
        llm_cache_key = rendered_prompt
        cached_llm_response = None
        cache_hit = False

        if current_app.config.get("CACHE_ENABLED", True):
            cached_llm_response = llm_cache.get(llm_cache_key)

        if cached_llm_response:
            cache_hit = True
            llm_response = cached_llm_response
            profiler.record_stage("llm_generation", 0.0001)
            logger.info(f"LLM Generation CACHE HIT | QueryHash: {query_hash} | PromptSHA256: {prompt_hash[:12]}...")
        else:
            with profiler.profile("llm_generation"):
                llm_service = LLMService()
                llm_response = llm_service.generate(rendered_prompt)

            if current_app.config.get("CACHE_ENABLED", True):
                llm_cache.set(llm_cache_key, llm_response)

        # JSON Serialization latency profile
        with profiler.profile("json_serialization"):
            timing_breakdown = profiler.get_breakdown()
            total_latency = timing_breakdown["total"]

            response_payload = {
                "success": True,
                "request_id": llm_response["request_id"],
                "query": clean_query,
                "answer": llm_response["answer"],
                "model": llm_response["model"],
                "prompt_hash": prompt_hash,
                "cache_hit": cache_hit,
                "latency": total_latency,
                "llm_latency": timing_breakdown.get("llm_generation", 0.0),
                "prompt_tokens": llm_response.get("prompt_tokens", 0),
                "completion_tokens": llm_response.get("completion_tokens", 0),
                "estimated_tokens": llm_response.get("total_tokens", 0),
                "finish_reason": llm_response.get("finish_reason", "stop"),
                "timing_breakdown": timing_breakdown,
                "citations": citations,
                "results": included_chunks
            }

        # Structured Observability Log (Never logging key, query text, or document text)
        logger.info(
            f"Chat Endpoint Success | "
            f"ReqID: {llm_response['request_id']} | "
            f"QueryHash: {query_hash} | "
            f"CacheHit: {cache_hit} | "
            f"TotalLatency: {total_latency:.4f}s | "
            f"LLMLatency: {timing_breakdown.get('llm_generation', 0.0):.4f}s | "
            f"PromptTokens: {llm_response.get('prompt_tokens', 0)} | "
            f"CompletionTokens: {llm_response.get('completion_tokens', 0)}"
        )

        return jsonify(response_payload), 200

    except LLMAuthenticationError as e:
        logger.warning(f"LLM Authentication Error in chat endpoint: {e}")
        return jsonify({
            "success": False,
            "message": f"NVIDIA API Authentication failed: {str(e)}"
        }), 401

    except LLMTimeoutError as e:
        logger.warning(f"LLM Timeout Error in chat endpoint: {e}")
        return jsonify({
            "success": False,
            "message": f"NVIDIA API request timed out: {str(e)}"
        }), 504

    except (LLMServiceError, PromptBuilderError) as e:
        logger.warning(f"RAG Chat pipeline error: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400

    except Exception as e:
        logger.exception("Unexpected error in RAG chat endpoint")
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500
