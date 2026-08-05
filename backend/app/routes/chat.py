import time
import hashlib
import logging
from typing import Dict, Any, List, Optional
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
from app.services.session_service import (
    create_session,
    get_session,
    append_message_turn,
    format_multi_turn_history,
    list_sessions,
    delete_session,
    load_session_history
)
from app.services.retrieval_log_service import save_retrieved_chunks

logger = logging.getLogger("rag_backend.routes.chat")

chat_bp = Blueprint("chat", __name__)

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
CROSS_ENCODER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

@chat_bp.route("/chat/health", methods=["GET"])
def chat_health_endpoint():
    """
    GET endpoint checking local LLM configuration, model readiness, PostgreSQL session memory, cache stats, and uptime.
    """
    try:
        service = LLMService()
        health_info = service.health_check()

        startup_time = current_app.config.get("STARTUP_TIME", time.time())
        uptime_seconds = round(time.time() - startup_time, 2)

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

        return jsonify({
            "success": True,
            **health_info,
            "readiness": {
                "embedding_loaded": embedding_loaded,
                "cross_encoder_loaded": cross_encoder_loaded,
                "bm25_ready": bm25_ready,
                "faiss_ready": faiss_ready,
                "prompt_template_loaded": True,
                "session_service": "postgres_ready",
                "nvidia_api_configured": health_info.get("configured", False)
            },
            "embedding_model": EMBEDDING_MODEL_NAME,
            "cross_encoder_model": CROSS_ENCODER_MODEL_NAME,
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

@chat_bp.route("/chat/new", methods=["POST"])
def chat_new_session_endpoint():
    """
    POST endpoint creating a new research session in PostgreSQL.
    Returns: JSON with session_id
    """
    try:
        data = request.get_json(silent=True) or {}
        title = data.get("title")
        session = create_session(title=title)
        return jsonify({
            "success": True,
            "session_id": session.session_uuid,
            "session": session.to_dict()
        }), 201
    except Exception as e:
        logger.exception("Error creating new chat session")
        return jsonify({
            "success": False,
            "message": f"Failed to create new session: {str(e)}"
        }), 500

@chat_bp.route("/chat/sessions", methods=["GET"])
def chat_list_sessions_endpoint():
    """
    GET endpoint returning all persistent research sessions sorted by latest activity.
    """
    try:
        sessions = list_sessions()
        serialized = [s.to_dict() for s in sessions]
        return jsonify({
            "success": True,
            "sessions": serialized
        }), 200
    except Exception as e:
        logger.exception("Error listing chat sessions")
        return jsonify({
            "success": False,
            "message": f"Failed to list sessions: {str(e)}"
        }), 500

@chat_bp.route("/chat/history/<session_id>", methods=["GET"])
def chat_get_history_endpoint(session_id: str):
    """
    GET endpoint returning stored message history for a specific research session from PostgreSQL.
    """
    try:
        history_payload = load_session_history(session_id)
        return jsonify({
            "success": True,
            "session_id": session_id,
            "title": history_payload.get("title", "New Research Session"),
            "messages": history_payload.get("messages", [])
        }), 200
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 404
    except Exception as e:
        logger.exception(f"Error retrieving history for session {session_id}")
        return jsonify({
            "success": False,
            "message": f"Failed to retrieve history: {str(e)}"
        }), 500

@chat_bp.route("/chat/<session_id>", methods=["DELETE"])
def chat_delete_session_endpoint(session_id: str):
    """
    DELETE endpoint deleting a specific research session from PostgreSQL (cascading messages & logs).
    """
    try:
        deleted = delete_session(session_id)
        if not deleted:
            return jsonify({
                "success": False,
                "message": f"Session '{session_id}' not found."
            }), 404

        return jsonify({
            "success": True,
            "session_id": session_id,
            "message": "Research session deleted successfully."
        }), 200
    except Exception as e:
        logger.exception(f"Error deleting session {session_id}")
        return jsonify({
            "success": False,
            "message": f"Failed to delete session: {str(e)}"
        }), 500

@chat_bp.route("/chat", methods=["POST"])
def chat_endpoint():
    """
    POST endpoint executing the multi-turn RAG Generation pipeline with PostgreSQL memory:
      User Query → Session Resolution → History Assembly → Hybrid Retrieval → Cross-Encoder Reranking
      → LLM Generation → Transactional Persistence (Message & RetrievalLogs) → Response.
    """
    data = request.get_json(silent=True) or {}
    query = data.get("question") or data.get("query")
    session_id = data.get("session_id")
    top_k = data.get("top_k")
    template_version = data.get("template_version")

    if not query or not str(query).strip():
        return jsonify({
            "success": False,
            "message": "Missing or empty 'question' or 'query' parameter in request body."
        }), 400

    clean_query = str(query).strip()
    profiler = PipelineProfiler()
    query_hash = hashlib.sha256(clean_query.encode("utf-8")).hexdigest()[:12]

    # Step 1: Session Resolution & Multi-Turn History Loading from PostgreSQL
    with profiler.profile("session_retrieval"):
        session_record = get_session(session_id) if session_id else None
        if not session_record:
            session_record = create_session()
            session_id = session_record.session_uuid
        else:
            session_id = session_record.session_uuid

        conversation_history = format_multi_turn_history(session_id, max_turns=10)

    try:
        rerank_service = CrossEncoderService()
        actual_top_k = top_k if (isinstance(top_k, int) and top_k > 0) else rerank_service._get_default_top_k()

        # Step 2: Retrieval & Reranking Pipeline
        t_hybrid_0 = time.perf_counter()
        with profiler.profile("hybrid_retrieval"):
            hybrid_service = HybridRetrievalService()
            candidate_pool_limit = current_app.config.get("RERANK_CANDIDATE_POOL", 20)
            candidate_top_k = max(actual_top_k, candidate_pool_limit)
            candidates = hybrid_service.search(clean_query, top_k=candidate_top_k)
        t_hybrid_1 = time.perf_counter()
        hybrid_ms = (t_hybrid_1 - t_hybrid_0) * 1000.0

        if hasattr(hybrid_service, "last_profile") and isinstance(getattr(hybrid_service, "last_profile"), dict):
            profiler.record_stage("semantic_retrieval", float(hybrid_service.last_profile.get("semantic_retrieval", 0.0)))
            profiler.record_stage("bm25_retrieval", float(hybrid_service.last_profile.get("bm25_retrieval", 0.0)))
            profiler.record_stage("rrf_merge", float(hybrid_service.last_profile.get("rrf_merge", 0.0)))

        t_cross_0 = time.perf_counter()
        with profiler.profile("cross_encoder"):
            reranked_results = rerank_service.rerank(clean_query, candidates, top_k=actual_top_k)
        t_cross_1 = time.perf_counter()
        cross_encoder_ms = (t_cross_1 - t_cross_0) * 1000.0
        total_retrieval_ms = hybrid_ms + cross_encoder_ms

        with profiler.profile("prompt_builder"):
            prompt_service = PromptBuilderService()
            prompt_result = prompt_service.build_prompt(
                query=clean_query,
                retrieval_results=reranked_results,
                template_version=template_version,
                conversation_history=conversation_history
            )

        included_chunks = prompt_result["results"]
        rendered_prompt = prompt_result["prompt"]
        prompt_hash = prompt_result["prompt_hash"]

        # Step 3: Extract Citations & Build Safe Serializable Chunks
        citations = []
        clean_included_chunks = []
        for chunk in included_chunks:
            doc_id_val = str(chunk.get("document_id") or chunk.get("document_uuid") or "")
            chunk_id_val = str(chunk.get("chunk_id") or chunk.get("chunk_uuid") or "")
            doc_name_val = str(chunk.get("document_name") or chunk.get("filename") or "Unknown")
            page_val = int(chunk.get("page_number", 1))
            text_val = str(chunk.get("text", ""))

            scores_dict = chunk.get("scores") or {}
            sem_sc = float(scores_dict.get("semantic", chunk.get("semantic_score", 0.0)))
            bm_sc = float(scores_dict.get("bm25", chunk.get("bm25_score", 0.0)))
            rrf_sc = float(scores_dict.get("rrf", chunk.get("rrf_score", 0.0)))
            cross_sc = float(scores_dict.get("cross_encoder", chunk.get("reranker_score", chunk.get("score", 0.0))))

            c_dict = {
                "document_id": doc_id_val,
                "document_name": doc_name_val,
                "chunk_id": chunk_id_val,
                "page_number": page_val,
                "text": text_val,
                "scores": {
                    "semantic": sem_sc,
                    "bm25": bm_sc,
                    "rrf": rrf_sc,
                    "cross_encoder": cross_sc
                }
            }
            clean_included_chunks.append(c_dict)
            citations.append({
                "document_name": doc_name_val,
                "page_number": page_val,
                "chunk_id": chunk_id_val,
                "text": text_val
            })

        # Step 4: Check LLM Cache / Execute NVIDIA LLM API
        llm_cache_key = rendered_prompt
        cached_llm_response = None
        cache_hit = False

        if current_app.config.get("CACHE_ENABLED", True):
            cached_llm_response = llm_cache.get(llm_cache_key)

        if cached_llm_response:
            cache_hit = True
            llm_response = cached_llm_response
            profiler.record_stage("nvidia_prep", 0.0001)
            profiler.record_stage("nvidia_network", 0.0001)
            profiler.record_stage("llm_generation", 0.0001)
            logger.info(f"LLM Generation CACHE HIT | QueryHash: {query_hash} | Session: {session_id[:8]}")
        else:
            with profiler.profile("nvidia_prep"):
                llm_service = LLMService()

            with profiler.profile("llm_generation"):
                t_net_0 = time.perf_counter()
                llm_response = llm_service.generate(rendered_prompt)
                t_net_1 = time.perf_counter()
                profiler.record_stage("nvidia_network", round(t_net_1 - t_net_0, 4))

            if current_app.config.get("CACHE_ENABLED", True):
                llm_cache.set(llm_cache_key, llm_response)

        # Step 5: Transactional Persistence in PostgreSQL
        with profiler.profile("json_serialization"):
            timing_breakdown = profiler.get_breakdown()
            total_latency = timing_breakdown["total"]

            # 5a. Append Message turn into PostgreSQL
            message_obj, updated_session = append_message_turn(
                session_id_or_uuid=session_id,
                user_question=clean_query,
                assistant_answer=str(llm_response.get("answer", "")),
                latency=total_latency,
                token_count=int(llm_response.get("total_tokens", 0)),
                role="assistant"
            )

            # 5b. Persist evidence attribution logs in PostgreSQL
            save_retrieved_chunks(
                message_id=message_obj.id,
                chunks=clean_included_chunks,
                strategy="Hybrid RRF"
            )

            conversation_length = len(updated_session.messages) if updated_session.messages else 1

            retrieval_latency_ms = {
                "hybrid_ms": round(hybrid_ms, 2),
                "cross_encoder_ms": round(cross_encoder_ms, 2),
                "total_ms": round(total_retrieval_ms, 2)
            }

            formatted_summary = (
                f"Session Retrieval: {timing_breakdown.get('ms', {}).get('session_retrieval_ms', 0):.2f} ms\n"
                f"Hybrid Retrieval: {retrieval_latency_ms['hybrid_ms']:.2f} ms\n"
                f"Cross Encoder: {retrieval_latency_ms['cross_encoder_ms']:.2f} ms\n"
                f"Total Retrieval: {retrieval_latency_ms['total_ms']:.2f} ms\n"
                f"Prompt Builder: {timing_breakdown.get('ms', {}).get('prompt_builder_ms', 0):.2f} ms\n"
                f"LLM Generation: {timing_breakdown.get('ms', {}).get('llm_generation_ms', 0):.2f} ms\n"
                f"Total Execution: {timing_breakdown.get('ms', {}).get('total_ms', 0):.2f} ms"
            )

            response_payload = {
                "success": True,
                "session_id": session_id,
                "question": clean_query,
                "query": clean_query,
                "answer": str(llm_response.get("answer", "")),
                "citations": citations,
                "retrieved_chunks": clean_included_chunks,
                "results": clean_included_chunks,
                "latency": round(total_latency, 3),
                "retrieval_latency_ms": retrieval_latency_ms,
                "embedding_model": EMBEDDING_MODEL_NAME,
                "cross_encoder_model": CROSS_ENCODER_MODEL_NAME,
                "conversation_length": conversation_length,
                "conversation_turns": conversation_length,
                "request_id": str(llm_response.get("request_id", "")),
                "model": str(llm_response.get("model", "")),
                "finish_reason": str(llm_response.get("finish_reason", "stop")),
                "prompt_hash": prompt_hash,
                "cache_hit": cache_hit,
                "llm_latency": round(timing_breakdown.get("llm_generation", 0.0), 3),
                "prompt_tokens": int(llm_response.get("prompt_tokens", 0)),
                "completion_tokens": int(llm_response.get("completion_tokens", 0)),
                "estimated_tokens": int(llm_response.get("total_tokens", 0)),
                "timing_breakdown": timing_breakdown,
                "timing_summary": formatted_summary
            }

        logger.info(
            f"Chat Endpoint Success | "
            f"SessionID: {session_id[:12]}... | "
            f"MessageID: {message_obj.id} | "
            f"ConversationLength: {conversation_length} | "
            f"RetrievalTotal: {retrieval_latency_ms['total_ms']}ms | "
            f"Latency: {total_latency:.4f}s"
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
