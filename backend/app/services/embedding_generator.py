import os
import gc
import time
import json
import logging
from datetime import datetime, timezone
import numpy as np
from flask import current_app
from app.services.embedding import EmbeddingService, EmbeddingServiceError
from app.config import get_config

logger = logging.getLogger("rag_backend.embedding_generator")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHUNKS_DIR = os.path.join(BASE_DIR, "data", "chunks")
EMBEDDINGS_DIR = os.path.join(BASE_DIR, "data", "embeddings")

# Ensure embeddings directory exists
os.makedirs(EMBEDDINGS_DIR, exist_ok=True)

def generate_embeddings_for_document(doc_id: str, batch_size: int = None) -> dict:
    """
    Generates embeddings for all chunks of a document with ultra-low RAM footprint.
    Preallocates the output numpy matrix, processes texts in micro-batches (default size 4),
    frees batch memory immediately, and invokes gc.collect().
    """
    # 1. Resolve batch size from arguments, app config, or default (4 for Render Free 512MB RAM)
    if batch_size is None:
        try:
            if current_app and hasattr(current_app, "config"):
                batch_size = current_app.config.get("EMBEDDING_BATCH_SIZE", 4)
        except (RuntimeError, ImportError):
            pass
            
        if batch_size is None:
            try:
                config = get_config()
                batch_size = getattr(config, "EMBEDDING_BATCH_SIZE", 4)
            except Exception:
                batch_size = 4

    logger.info(f"Starting memory-optimized embedding generation for doc {doc_id} (batch size: {batch_size})")
    start_time = time.time()

    # Paths
    chunks_path = os.path.join(CHUNKS_DIR, f"{doc_id}_chunks.json")
    npy_path = os.path.join(EMBEDDINGS_DIR, f"{doc_id}_embeddings.npy")
    meta_path = os.path.join(EMBEDDINGS_DIR, f"{doc_id}_meta.json")

    if not os.path.exists(chunks_path):
        err_msg = f"Chunks file not found for document {doc_id}: {chunks_path}"
        logger.error(err_msg)
        raise FileNotFoundError(err_msg)

    try:
        with open(chunks_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)
    except Exception as e:
        logger.exception(f"Error loading chunks for document {doc_id}")
        raise ValueError(f"Failed to read chunks file: {str(e)}") from e

    num_chunks = len(chunks)
    embedding_service = EmbeddingService()
    model_info = embedding_service.get_model_info()
    model_name = model_info["model_name"]
    dimension = model_info["dimension"]

    logger.info(f"Loaded {num_chunks} chunks. Model: {model_name} ({dimension}d). Preallocating matrix...")

    if num_chunks == 0:
        logger.warning(f"No chunks found for document {doc_id}. Creating empty embeddings matrix.")
        embeddings_matrix = np.empty((0, dimension), dtype=np.float32)
    else:
        # Preallocate float32 numpy array directly
        embeddings_matrix = np.zeros((num_chunks, dimension), dtype=np.float32)
        try:
            for i in range(0, num_chunks, batch_size):
                end_i = min(i + batch_size, num_chunks)
                # Slice texts on demand without copying entire dataset
                batch_texts = [chunks[j].get("text", "") for j in range(i, end_i)]
                batch_embeddings = embedding_service.embed_batch(batch_texts)
                
                # Copy directly into preallocated matrix
                embeddings_matrix[i:end_i, :] = batch_embeddings
                
                # Immediately release micro-batch intermediate variables
                del batch_texts
                del batch_embeddings
                gc.collect()

        except Exception as e:
            logger.exception(f"Error encoding chunk batch for document {doc_id}")
            raise EmbeddingServiceError(f"Embedding encoding failed: {str(e)}") from e

    # Validate generated matrix shape
    expected_shape = (num_chunks, dimension)
    if embeddings_matrix.shape != expected_shape:
        err_msg = f"Embedding shape mismatch: generated {embeddings_matrix.shape}, expected {expected_shape}"
        logger.error(err_msg)
        raise EmbeddingServiceError(err_msg)

    # Save numpy binary file
    try:
        np.save(npy_path, embeddings_matrix)
        logger.info(f"Saved embeddings array to {npy_path}")
    except Exception as e:
        logger.exception(f"Failed to save embeddings array to {npy_path}")
        raise EmbeddingServiceError(f"Failed to save embeddings .npy file: {str(e)}") from e

    # Save embedding metadata JSON file
    emb_metadata = {
        "document_id": doc_id,
        "embedding_model": model_name,
        "embedding_dimension": dimension,
        "chunk_count": num_chunks,
        "embedding_version": "1.0",
        "created_timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }

    try:
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(emb_metadata, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved embedding metadata to {meta_path}")
    except Exception as e:
        logger.exception(f"Failed to save embedding metadata to {meta_path}")
        raise EmbeddingServiceError(f"Failed to save embedding metadata JSON: {str(e)}") from e

    elapsed_time = time.time() - start_time
    logger.info(f"Successfully generated embeddings for {num_chunks} chunks in {elapsed_time:.2f}s")

    # Final garbage collection cleanup before returning
    del embeddings_matrix
    del chunks
    gc.collect()

    return {
        "success": True,
        "embedding_model": model_name,
        "embedding_dimension": dimension,
        "chunk_count": num_chunks,
        "elapsed_seconds": elapsed_time
    }
