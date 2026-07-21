import logging
import time
from typing import Dict, Any

logger = logging.getLogger("rag_backend.services.warmup")

def warmup_services(app=None) -> Dict[str, Any]:
    """
    Eagerly initializes pipeline models and index structures on application startup.
    
    Eliminates cold-start latency penalties on first user request.
    """
    t0 = time.time()
    logger.info("Starting pipeline warmup sequence...")

    status = {
        "embedding_loaded": False,
        "cross_encoder_loaded": False,
        "bm25_ready": False,
        "faiss_ready": False,
        "prompt_template_loaded": False,
        "nvidia_api_configured": False,
        "warmup_time_seconds": 0.0
    }

    # 1. Warm-up Embedding Model
    try:
        from app.services.embedding import EmbeddingService
        emb_svc = EmbeddingService()
        emb_svc.get_model()
        status["embedding_loaded"] = True
        logger.info("Warmup: SentenceTransformer embedding model ready.")
    except Exception as e:
        logger.warning(f"Warmup: Embedding model initialization deferred: {e}")


    # 2. Warm-up Cross Encoder Model
    try:
        from app.services.cross_encoder import CrossEncoderService
        ce_svc = CrossEncoderService()
        if hasattr(ce_svc, "get_model"):
            ce_svc.get_model()
            status["cross_encoder_loaded"] = True
            logger.info("Warmup: Cross-Encoder model ready.")
    except Exception as e:
        logger.warning(f"Warmup: Cross-Encoder model initialization deferred: {e}")

    # 3. Warm-up Prompt Builder Templates
    try:
        from app.services.prompt_builder import PromptBuilderService
        pb = PromptBuilderService()
        pb.load_template("rag_prompt_v1")
        status["prompt_template_loaded"] = True
        logger.info("Warmup: Prompt template engine ready.")
    except Exception as e:
        logger.warning(f"Warmup: Prompt template initialization deferred: {e}")

    # 4. Warm-up BM25 Index
    try:
        from app.services.bm25_index import get_bm25_index_service
        bm25_service = get_bm25_index_service()
        status["bm25_ready"] = bool(getattr(bm25_service, "_index", None) is not None or getattr(bm25_service, "chunk_count", 0) > 0)
        logger.info("Warmup: BM25 index ready.")
    except Exception as e:
        logger.warning(f"Warmup: BM25 index initialization deferred: {e}")

    # 5. Warm-up FAISS Vector Index
    try:
        from app.services.vector_index import get_vector_index_service
        vector_service = get_vector_index_service()
        status["faiss_ready"] = bool(getattr(vector_service, "_index", None) is not None or getattr(vector_service, "total_vectors", 0) > 0)
        logger.info("Warmup: FAISS vector index ready.")
    except Exception as e:
        logger.warning(f"Warmup: FAISS vector index initialization deferred: {e}")

    # 6. Verify NVIDIA API configuration
    try:
        from app.services.nvidia_client import NVIDIAClient
        client = NVIDIAClient()
        status["nvidia_api_configured"] = bool(client.api_key and client.api_key.strip() != "your_nvidia_api_key_here")
        logger.info(f"Warmup: NVIDIA API configured: {status['nvidia_api_configured']}.")
    except Exception as e:
        logger.warning(f"Warmup: NVIDIA client configuration check failed: {e}")

    status["warmup_time_seconds"] = round(time.time() - t0, 4)
    logger.info(f"Pipeline warmup sequence completed in {status['warmup_time_seconds']}s.")
    return status
