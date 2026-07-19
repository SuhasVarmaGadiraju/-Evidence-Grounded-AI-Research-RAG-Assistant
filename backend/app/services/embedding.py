import time
import logging
import numpy as np
import threading
from sentence_transformers import SentenceTransformer
from flask import current_app
from app.config import get_config

logger = logging.getLogger("rag_backend.embedding")

class EmbeddingServiceError(Exception):
    """Exception raised for errors in the EmbeddingService."""
    pass

class EmbeddingService:
    """
    Service responsible for loading and managing the SentenceTransformer model.
    Uses the Singleton pattern to ensure only one instance of the model is loaded in memory.
    """
    _instance = None
    _model = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_name=None):
        # Prevent re-initialization of initialized fields
        if hasattr(self, "_initialized") and self._initialized:
            # If a different model name is passed after loading, warn the user
            if model_name is not None and model_name != self._get_model_name():
                logger.warning(
                    f"Embedding model is already loaded/configured as '{self._get_model_name()}'. "
                    f"Ignoring request to initialize with model '{model_name}'."
                )
            return

        self._initialized = True
        self.model_name = model_name

    def _get_model_name(self) -> str:
        """Determines the model name to load from config, environment, or default."""
        if self.model_name:
            return self.model_name

        # 1. Attempt to read from flask current_app configuration
        try:
            if current_app and hasattr(current_app, "config"):
                cfg_model = current_app.config.get("EMBEDDING_MODEL")
                if cfg_model:
                    return cfg_model
        except (RuntimeError, ImportError):
            # Working outside of a Flask application context or Flask is not installed
            pass

        # 2. Fall back to reading from app.config.get_config()
        try:
            config = get_config()
            cfg_model = getattr(config, "EMBEDDING_MODEL", None)
            if cfg_model:
                return cfg_model
        except Exception:
            pass

        # 3. Hard default
        return "all-MiniLM-L6-v2"

    def get_model(self) -> SentenceTransformer:
        """
        Lazily loads and returns the SentenceTransformer model instance.
        Ensures the model is loaded only once across the application lifecycle.
        """
        if EmbeddingService._model is None:
            with EmbeddingService._lock:
                if EmbeddingService._model is None:
                    model_name = self._get_model_name()
                    logger.info(f"Initializing SentenceTransformer model '{model_name}' (lazy load)...")
                    start_time = time.time()
                    try:
                        # Load the model and save to the class-level cache variable
                        EmbeddingService._model = SentenceTransformer(model_name)
                        elapsed = time.time() - start_time
                        logger.info(f"Successfully loaded model '{model_name}' in {elapsed:.2f} seconds.")
                    except Exception as e:
                        logger.exception(f"Failed to load SentenceTransformer model '{model_name}'")
                        raise EmbeddingServiceError(f"Failed to load embedding model: {str(e)}") from e
        return EmbeddingService._model

    def embed_text(self, text: str) -> np.ndarray:
        """
        Generates embedding for a single text input.

        Args:
            text (str): The input text to embed.

        Returns:
            np.ndarray: A 1D float32 numpy array representing the embedding vector.
        """
        if not isinstance(text, str):
            logger.error("Single text input is not a string.")
            raise EmbeddingServiceError("Input text must be a string.")

        if not text.strip():
            logger.warning("Empty or whitespace-only text passed for embedding. Returning zero vector.")
            dim = self.get_dimension()
            return np.zeros(dim, dtype=np.float32)

        model = self.get_model()
        logger.info(f"Generating embedding for single text (length: {len(text)})")
        start_time = time.time()
        try:
            embedding = model.encode(text, convert_to_numpy=True, show_progress_bar=False)
            elapsed = time.time() - start_time
            logger.info(f"Generated single embedding in {elapsed:.4f} seconds.")
            return embedding.astype(np.float32)
        except Exception as e:
            logger.exception("Error generating single text embedding")
            raise EmbeddingServiceError(f"Error generating embedding: {str(e)}") from e

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """
        Generates embeddings for a batch of text inputs.

        Args:
            texts (list[str]): A list of strings to embed.

        Returns:
            np.ndarray: A 2D float32 numpy array of shape (num_texts, dimension).
        """
        if not isinstance(texts, list):
            logger.error("Batch input is not a list.")
            raise EmbeddingServiceError("Input to embed_batch must be a list of strings.")

        if not all(isinstance(t, str) for t in texts):
            logger.error("Not all elements in batch input are strings.")
            raise EmbeddingServiceError("All elements in the batch must be strings.")

        if not texts:
            logger.info("Empty list passed to embed_batch. Returning empty 2D array.")
            dim = self.get_dimension()
            return np.empty((0, dim), dtype=np.float32)

        model = self.get_model()
        logger.info(f"Generating embeddings for batch of size {len(texts)}")
        start_time = time.time()
        try:
            embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            elapsed = time.time() - start_time
            logger.info(f"Generated batch embeddings in {elapsed:.4f} seconds.")
            return embeddings.astype(np.float32)
        except Exception as e:
            logger.exception("Error generating batch text embeddings")
            raise EmbeddingServiceError(f"Error generating batch embeddings: {str(e)}") from e

    def get_dimension(self) -> int:
        """
        Retrieves the embedding dimension of the loaded model.

        Returns:
            int: The size of the embedding vectors produced by this model.
        """
        model = self.get_model()
        try:
            return int(model.get_sentence_embedding_dimension())
        except Exception as e:
            logger.warning(f"Could not retrieve model dimension via get_sentence_embedding_dimension(): {e}")
            # Fallback by encoding a dummy string to get the shape
            try:
                dummy_emb = model.encode("dummy", convert_to_numpy=True, show_progress_bar=False)
                return int(dummy_emb.shape[0])
            except Exception as dummy_err:
                logger.error(f"Fallback dimension detection failed: {dummy_err}")
                raise EmbeddingServiceError("Unable to retrieve embedding model dimension.") from dummy_err

    def get_model_info(self) -> dict:
        """
        Retrieves model information such as name, dimension, and maximum sequence length.

        Returns:
            dict: Metadata about the currently configured embedding model.
        """
        model = self.get_model()
        model_name = self._get_model_name()
        dimension = self.get_dimension()
        max_seq_length = getattr(model, "max_seq_length", None)

        return {
            "model_name": model_name,
            "dimension": dimension,
            "max_seq_length": max_seq_length
        }
