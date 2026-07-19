import os
import time
import json
import logging
from flask import current_app
from app.services.base_retriever import BaseRetriever, RetrievalResult
from app.services.query_embedding import QueryEmbeddingService, QueryEmbeddingError
from app.services.vector_index import get_vector_index_service, VectorIndexServiceError
from app.config import get_config

logger = logging.getLogger("rag_backend.semantic_retrieval")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
METADATA_DIR = os.path.join(BASE_DIR, "data", "metadata")

class SemanticRetrievalError(Exception):
    """Exception raised for errors in the SemanticRetrievalService."""
    pass

class SemanticRetrievalService(BaseRetriever):
    """
    Coordinating service for executing semantic search across the vector store.
    Uses the QueryEmbeddingService to generate queries and VectorIndexService
    to execute nearest-neighbor inner-product searches.
    """
    def __init__(self):
        self.query_embedding_service = QueryEmbeddingService()
        self.vector_index_service = get_vector_index_service()
        self._doc_name_cache = {} # local cache to optimize repeated document metadata requests

    def _get_default_top_k(self) -> int:
        """Resolves the default top_k value from configuration files."""
        try:
            if current_app and hasattr(current_app, "config"):
                return current_app.config.get("DEFAULT_TOP_K", 5)
        except (RuntimeError, ImportError):
            pass
            
        try:
            config = get_config()
            return getattr(config, "DEFAULT_TOP_K", 5)
        except Exception:
            return 5

    def _lookup_document_name(self, doc_id: str) -> str:
        """Looks up the original filename for a document ID, caching results in memory."""
        if not doc_id:
            return "Unknown Document"
            
        if doc_id in self._doc_name_cache:
            return self._doc_name_cache[doc_id]

        meta_path = os.path.join(METADATA_DIR, f"{doc_id}_meta.json")
        if not os.path.exists(meta_path):
            return "Unknown Document"

        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            original_filename = meta.get("original_filename", "Unknown Document")
            self._doc_name_cache[doc_id] = original_filename
            return original_filename
        except Exception as e:
            logger.warning(f"Failed to load document metadata for {doc_id}: {e}")
            return "Unknown Document"

    def search(self, query: str, top_k: int = None) -> list[dict]:
        """
        Executes semantic search and maps vector results back to structured chunk metadata.
        
        Args:
            query (str): The search query.
            top_k (int, optional): The number of matching chunks to retrieve.
            
        Returns:
            list[dict]: Sorted, ranked list of matches containing similarity scores and document details.
        """
        start_time = time.time()
        
        # 1. Gracefully handle empty queries
        if not query or not query.strip():
            logger.warning("Empty search query received. Returning empty retrieval list.")
            return []

        # 2. Resolve and validate top_k parameters
        if top_k is None or not isinstance(top_k, int) or top_k <= 0:
            if top_k is not None:
                logger.warning(f"Invalid top_k value '{top_k}' provided. Falling back to default.")
            top_k = self._get_default_top_k()

        logger.info(f"Initiating semantic search for query (length: {len(query)}), top_k: {top_k}")

        try:
            # 3. Generate normalized query embedding
            query_vector = self.query_embedding_service.generate_query_embedding(query)
            
            # 4. Perform vector search in FAISS Index
            # Exposes: chunk_id, document_id, text, page_number, score
            raw_matches = self.vector_index_service.search(query_vector, k=top_k)
            
            # 5. Format results and map document details
            formatted_results = []
            for rank_idx, match in enumerate(raw_matches):
                doc_id = match.get("document_id")
                doc_name = self._lookup_document_name(doc_id)
                
                formatted_results.append(
                    RetrievalResult(
                        rank=rank_idx + 1,
                        score=float(match.get("score", 0.0)),
                        retrieval_type="semantic",
                        document_id=doc_id,
                        document_name=doc_name,
                        page_number=match.get("page_number", 0),
                        chunk_id=match.get("chunk_id"),
                        text=match.get("text", "")
                    )
                )
                
            elapsed_time = time.time() - start_time
            logger.info(f"Completed semantic search in {elapsed_time:.4f} seconds. Found {len(formatted_results)} matches.")
            return formatted_results

        except QueryEmbeddingError as qe:
            logger.error(f"Failed to generate query embedding: {qe}")
            raise SemanticRetrievalError(f"Embedding generation failure: {str(qe)}") from qe
        except VectorIndexServiceError as ve:
            logger.error(f"Vector search query failed: {ve}")
            raise SemanticRetrievalError(f"Vector index search failure: {str(ve)}") from ve
        except Exception as e:
            logger.exception("Unexpected error during semantic retrieval")
            raise SemanticRetrievalError(f"Retrieval pipeline failed: {str(e)}") from e

    def retrieve(self, query: str, top_k: int = None) -> list[dict]:
        """Compatibility wrapper that delegates to search."""
        return self.search(query, top_k)

    def get_stats(self) -> dict:
        """Returns stats about the vector index (delegated to the FAISS service)."""
        try:
            return self.vector_index_service.get_index_stats()
        except Exception as e:
            logger.error(f"Failed to get vector index stats: {e}")
            return {"status": "error", "error": str(e)}

    def health_check(self) -> bool:
        """Checks if the vector index is loaded and healthy."""
        try:
            stats = self.get_stats()
            return stats.get("status") in ["active", "empty"]
        except Exception:
            return False
