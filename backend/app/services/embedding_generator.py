import os
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
    Generates embeddings for all chunks of a specific document ID.
    
    Reads chunks from data/chunks/{doc_id}_chunks.json, passes them to
    EmbeddingService in batches, saves the final matrix to
    data/embeddings/{doc_id}_embeddings.npy, and saves the metadata to
    data/embeddings/{doc_id}_meta.json.
    
    Args:
        doc_id (str): The unique document UUID.
        batch_size (int, optional): Number of chunks to encode in a single model call.
        
    Returns:
        dict: Embedding execution summary.
    """
    # 1. Resolve batch size from arguments, app config, or defaults
    if batch_size is None:
        try:
            if current_app and hasattr(current_app, "config"):
                batch_size = current_app.config.get("EMBEDDING_BATCH_SIZE", 32)
        except (RuntimeError, ImportError):
            pass
            
        if batch_size is None:
            try:
                config = get_config()
                batch_size = getattr(config, "EMBEDDING_BATCH_SIZE", 32)
            except Exception:
                batch_size = 32

    logger.info(f"Starting chunk embedding generation for doc {doc_id} (batch size: {batch_size})")
    start_time = time.time()

    # Paths
    chunks_path = os.path.join(CHUNKS_DIR, f"{doc_id}_chunks.json")
    npy_path = os.path.join(EMBEDDINGS_DIR, f"{doc_id}_embeddings.npy")
    meta_path = os.path.join(EMBEDDINGS_DIR, f"{doc_id}_meta.json")

    # 2. Check that chunks file exists
    if not os.path.exists(chunks_path):
        err_msg = f"Chunks file not found for document {doc_id}: {chunks_path}"
        logger.error(err_msg)
        raise FileNotFoundError(err_msg)

    # 3. Read chunk data
    try:
        with open(chunks_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)
    except Exception as e:
        logger.exception(f"Error loading chunks for document {doc_id}")
        raise ValueError(f"Failed to read chunks file: {str(e)}") from e

    # 4. Initialize embedding service and load configuration info
    embedding_service = EmbeddingService()
    model_info = embedding_service.get_model_info()
    model_name = model_info["model_name"]
    dimension = model_info["dimension"]

    logger.info(f"Loaded {len(chunks)} chunks. Model: {model_name} ({dimension}d)")

    # 5. Extract texts and generate embeddings
    texts = [chunk.get("text", "") for chunk in chunks]
    embeddings_list = []

    if not chunks:
        logger.warning(f"No chunks found for document {doc_id}. Creating empty embeddings matrix.")
        embeddings_matrix = np.empty((0, dimension), dtype=np.float32)
    else:
        try:
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                # Each batch_texts contains list of strings
                batch_embeddings = embedding_service.embed_batch(batch_texts)
                embeddings_list.append(batch_embeddings)
                
            # Concatenate list of matrices to a single numpy array
            embeddings_matrix = np.vstack(embeddings_list)
        except Exception as e:
            logger.exception(f"Error encoding chunk batch for document {doc_id}")
            raise EmbeddingServiceError(f"Embedding encoding failed: {str(e)}") from e

    # 6. Validate generated matrix shape
    expected_shape = (len(chunks), dimension)
    if embeddings_matrix.shape != expected_shape:
        err_msg = f"Embedding shape mismatch: generated {embeddings_matrix.shape}, expected {expected_shape}"
        logger.error(err_msg)
        raise EmbeddingServiceError(err_msg)

    # 7. Save numpy binary file
    try:
        np.save(npy_path, embeddings_matrix)
        logger.info(f"Saved embeddings array to {npy_path}")
    except Exception as e:
        logger.exception(f"Failed to save embeddings array to {npy_path}")
        raise EmbeddingServiceError(f"Failed to save embeddings .npy file: {str(e)}") from e

    # 8. Save embedding metadata JSON file
    emb_metadata = {
        "document_id": doc_id,
        "embedding_model": model_name,
        "embedding_dimension": dimension,
        "chunk_count": len(chunks),
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
    logger.info(f"Successfully generated embeddings for {len(chunks)} chunks in {elapsed_time:.2f}s")

    return {
        "success": True,
        "embedding_model": model_name,
        "embedding_dimension": dimension,
        "chunk_count": len(chunks),
        "elapsed_seconds": elapsed_time
    }
