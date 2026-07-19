import os
import time
import logging
import threading
from sentence_transformers import CrossEncoder
from flask import current_app
from app.services.base_retriever import RetrievalResult
from app.config import get_config

logger = logging.getLogger("rag_backend.cross_encoder")

class CrossEncoderServiceError(Exception):
    """Exception raised for errors in the CrossEncoderService."""
    pass

class CrossEncoderService:
    """
    Service responsible for loading and managing the CrossEncoder model.
    Uses the Singleton pattern to ensure only one instance of the model is loaded in memory.
    """
    _instance = None
    _model = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(CrossEncoderService, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_name=None):
        if hasattr(self, "_initialized") and self._initialized:
            if model_name is not None and model_name != self._get_model_name():
                logger.warning(
                    f"Cross-Encoder model is already loaded/configured as '{self._get_model_name()}'. "
                    f"Ignoring request to initialize with model '{model_name}'."
                )
            return

        self._initialized = True
        self.model_name = model_name

    def _get_model_name(self) -> str:
        """Determines the CrossEncoder model name to load from config or defaults."""
        if self.model_name:
            return self.model_name

        try:
            if current_app and hasattr(current_app, "config"):
                cfg_model = current_app.config.get("RERANK_MODEL")
                if cfg_model:
                    return cfg_model
        except (RuntimeError, ImportError):
            pass

        try:
            config = get_config()
            cfg_model = getattr(config, "RERANK_MODEL", None)
            if cfg_model:
                return cfg_model
        except Exception:
            pass

        return "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def _get_batch_size(self) -> int:
        """Determines the inference batch size from config or defaults."""
        try:
            if current_app and hasattr(current_app, "config"):
                return current_app.config.get("RERANK_BATCH_SIZE", 32)
        except (RuntimeError, ImportError):
            pass

        try:
            config = get_config()
            return getattr(config, "RERANK_BATCH_SIZE", 32)
        except Exception:
            pass

        return 32

    def _get_default_top_k(self) -> int:
        """Determines the default top_k value from config or defaults."""
        try:
            if current_app and hasattr(current_app, "config"):
                return current_app.config.get("RERANK_TOP_K", 5)
        except (RuntimeError, ImportError):
            pass

        try:
            config = get_config()
            return getattr(config, "RERANK_TOP_K", 5)
        except Exception:
            pass

        return 5

    def get_model(self) -> CrossEncoder:
        """Lazily loads and returns the CrossEncoder model instance."""
        if CrossEncoderService._model is None:
            with CrossEncoderService._lock:
                if CrossEncoderService._model is None:
                    model_name = self._get_model_name()
                    logger.info(f"Initializing CrossEncoder model '{model_name}' (lazy load)...")
                    start_time = time.time()
                    try:
                        # Load CrossEncoder and save to singleton variable
                        CrossEncoderService._model = CrossEncoder(model_name)
                        elapsed = time.time() - start_time
                        logger.info(f"Successfully loaded CrossEncoder model '{model_name}' in {elapsed:.2f} seconds.")
                    except Exception as e:
                        logger.exception(f"Failed to load CrossEncoder model '{model_name}'")
                        raise CrossEncoderServiceError(f"Failed to load Cross-Encoder: {str(e)}") from e
        return CrossEncoderService._model

    def rerank(self, query: str, candidates: list[RetrievalResult], top_k: int = None) -> list[RetrievalResult]:
        """
        Reranks a list of candidate chunk results for a query using the Cross-Encoder model.

        Args:
            query (str): The search query.
            candidates (list[RetrievalResult]): Chunks to rank.
            top_k (int, optional): The final number of matches to return.

        Returns:
            list[RetrievalResult]: Fused and reranked results.
        """
        # 1. Edge case: empty query or no candidates
        if not query or not query.strip():
            logger.warning("Empty query provided for reranking. Returning empty list.")
            return []

        if not candidates:
            logger.debug("No candidates provided for reranking. Returning empty list.")
            return []

        # 2. Resolve parameters
        if top_k is None or not isinstance(top_k, int) or top_k <= 0:
            if top_k is not None:
                logger.warning(f"Invalid top_k '{top_k}' for reranker. Falling back to default.")
            top_k = self._get_default_top_k()

        # 3. Model acquisition
        model = self.get_model()
        batch_size = self._get_batch_size()

        # 4. Perform batched CrossEncoder predictions
        logger.info(f"Reranking {len(candidates)} candidates for query length: {len(query)} (batch size: {batch_size})")
        sentence_pairs = [(query, c.text) for c in candidates]
        
        start_inference = time.time()
        try:
            scores = model.predict(sentence_pairs, batch_size=batch_size, show_progress_bar=False)
        except Exception as e:
            logger.exception("Error occurred during CrossEncoder prediction inference.")
            raise CrossEncoderServiceError(f"CrossEncoder inference failed: {str(e)}") from e
        inference_latency = time.time() - start_inference

        # 5. Map scores and sort
        for candidate, score in zip(candidates, scores):
            candidate.rerank_score = float(score)

        # Sort descending by rerank score, and break ties alphabetically on chunk_id
        sorted_candidates = sorted(
            candidates,
            key=lambda x: (-x.rerank_score, x.chunk_id)
        )

        # 6. Re-assign ranks based on new order and select top_k
        final_results = []
        for rank_idx, result in enumerate(sorted_candidates[:top_k]):
            result.rank = rank_idx + 1
            final_results.append(result)

        logger.info(
            f"Successfully reranked candidates. Top candidate: '{final_results[0].chunk_id}' "
            f"(Score: {final_results[0].rerank_score:.4f}). Inference latency: {inference_latency:.4f}s."
        )

        return final_results
