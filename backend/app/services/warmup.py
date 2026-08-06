import os
import logging
import time
from typing import Dict, Any

logger = logging.getLogger("rag_backend.services.warmup")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
REQUIRED_DIRS = [
    os.path.join(DATA_DIR, "raw"),
    os.path.join(DATA_DIR, "extracted"),
    os.path.join(DATA_DIR, "processed"),
    os.path.join(DATA_DIR, "chunks"),
    os.path.join(DATA_DIR, "embeddings"),
    os.path.join(DATA_DIR, "metadata"),
    os.path.join(DATA_DIR, "faiss"),
]

def warmup_services(app=None) -> Dict[str, Any]:
    """
    Application startup verification and optional model warmup sequence.
    
    In production environments (FLASK_ENV=production or ENABLE_WARMUP=False),
    heavy ML models are NOT loaded into memory at startup to keep memory <100MB.
    Instead, it verifies directories, configuration, API keys, and environment variables.
    """
    t0 = time.time()
    logger.info("Starting application startup verification sequence...")

    # Determine whether model eager loading should be skipped
    flask_env = os.getenv("FLASK_ENV", "production").lower()
    enable_warmup_env = os.getenv("ENABLE_WARMUP", "True").lower() in ("true", "1", "yes")

    if app and hasattr(app, "config"):
        is_production = app.config.get("FLASK_ENV") == "production" or not app.config.get("ENABLE_WARMUP", True)
    else:
        is_production = (flask_env == "production") or not enable_warmup_env

    # 1. Always verify storage directories exist
    for dir_path in REQUIRED_DIRS:
        os.makedirs(dir_path, exist_ok=True)

    status = {
        "production_mode": is_production,
        "directories_verified": True,
        "embedding_loaded": False,
        "cross_encoder_loaded": False,
        "bm25_ready": False,
        "faiss_ready": False,
        "prompt_template_loaded": False,
        "nvidia_api_configured": False,
        "warmup_time_seconds": 0.0
    }

    # 2. Check NVIDIA API configuration
    nvidia_key = os.getenv("NVIDIA_API_KEY", "")
    status["nvidia_api_configured"] = bool(nvidia_key and nvidia_key.strip() != "nvapi-your-nvidia-api-key-here")

    # If in production or ENABLE_WARMUP=False, skip model loading to maintain RAM <100MB
    if is_production:
        status["warmup_time_seconds"] = round(time.time() - t0, 4)
        logger.info(
            "Startup warmup skipped for production memory optimization (RAM footprint <100MB). "
            "ML models will load lazily on first query access."
        )
        return status

    # 3. Eager model loading for non-production environments with explicit ENABLE_WARMUP=True
    logger.info("Local development mode detected. Initializing models eagerly...")

    try:
        from app.services.embedding import EmbeddingService
        emb_svc = EmbeddingService()
        emb_svc.get_model()
        status["embedding_loaded"] = True
    except Exception as e:
        logger.warning(f"Warmup: Embedding model initialization deferred: {e}")

    try:
        from app.services.cross_encoder import CrossEncoderService
        ce_svc = CrossEncoderService()
        if hasattr(ce_svc, "get_model"):
            ce_svc.get_model()
            status["cross_encoder_loaded"] = True
    except Exception as e:
        logger.warning(f"Warmup: Cross-Encoder model initialization deferred: {e}")

    try:
        from app.services.prompt_builder import PromptBuilderService
        pb = PromptBuilderService()
        pb.load_template("rag_prompt_v1")
        status["prompt_template_loaded"] = True
    except Exception as e:
        logger.warning(f"Warmup: Prompt template initialization deferred: {e}")

    try:
        from app.services.bm25_index import get_bm25_index_service
        bm25_service = get_bm25_index_service()
        status["bm25_ready"] = bool(getattr(bm25_service, "_index", None) is not None or getattr(bm25_service, "chunk_count", 0) > 0)
    except Exception as e:
        logger.warning(f"Warmup: BM25 index initialization deferred: {e}")

    try:
        from app.services.vector_index import get_vector_index_service
        vector_service = get_vector_index_service()
        status["faiss_ready"] = bool(getattr(vector_service, "_index", None) is not None or getattr(vector_service, "total_vectors", 0) > 0)
    except Exception as e:
        logger.warning(f"Warmup: FAISS vector index initialization deferred: {e}")

    status["warmup_time_seconds"] = round(time.time() - t0, 4)
    logger.info(f"Pipeline warmup sequence completed in {status['warmup_time_seconds']}s.")
    return status
