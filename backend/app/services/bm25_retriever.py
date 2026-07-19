import os
import time
import logging
from flask import current_app
from app.services.base_retriever import BaseRetriever, RetrievalResult
from app.services.bm25_index import get_bm25_index_service
from app.config import get_config

logger = logging.getLogger("rag_backend.bm25_retriever")

class BM25RetrievalService(BaseRetriever):
    """
    Service responsible for executing sparse search queries over the BM25 index.
    Delegates all index operations (serialization, synchronization, memory caching) to BM25IndexService.
    """
    def __init__(self):
        self.index_service = get_bm25_index_service()

    def _get_default_top_k(self) -> int:
        """Resolves the default top_k value from configuration."""
        try:
            if current_app and hasattr(current_app, "config"):
                return current_app.config.get("BM25_DEFAULT_TOP_K", 5)
        except (RuntimeError, ImportError):
            pass
            
        try:
            config = get_config()
            return getattr(config, "BM25_DEFAULT_TOP_K", 5)
        except Exception:
            return 5

    def _get_max_query_length(self) -> int:
        """Resolves the maximum query character length limit to protect resource consumption."""
        try:
            if current_app and hasattr(current_app, "config"):
                return current_app.config.get("BM25_MAX_QUERY_LENGTH", 1000)
        except (RuntimeError, ImportError):
            pass
            
        try:
            config = get_config()
            return getattr(config, "BM25_MAX_QUERY_LENGTH", 1000)
        except Exception:
            return 1000

    def search(self, query: str, top_k: int = None) -> list[RetrievalResult]:
        """
        Executes sparse BM25 retrieval, returning ranked matches in the standard schema format.
        
        Args:
            query (str): The search query.
            top_k (int, optional): The number of top matches to retrieve.
            
        Returns:
            list[RetrievalResult]: Sorted, ranked list of matches.
        """
        start_time = time.time()

        # 1. Gracefully handle empty queries
        if not query or not query.strip():
            logger.warning("Empty search query received. Returning empty retrieval list.")
            return []

        # 2. Hardening: Enforce query length limits
        max_query_len = self._get_max_query_length()
        if len(query) > max_query_len:
            logger.warning(f"Query length ({len(query)}) exceeds limit ({max_query_len}). Truncating query.")
            query = query[:max_query_len]

        # 3. Synchronize the index if changes are detected in documents
        self.index_service.check_and_sync_index()

        # 4. Handle empty index
        if self.index_service.bm25 is None or not self.index_service._chunks:
            logger.warning("BM25 search queried on an empty or uninitialized index.")
            return []

        # 5. Resolve and validate top_k parameters
        if top_k is None or not isinstance(top_k, int) or top_k <= 0:
            if top_k is not None:
                logger.warning(f"Invalid top_k value '{top_k}' provided. Falling back to default.")
            top_k = self._get_default_top_k()

        logger.info(f"Initiating BM25 search. Query length: {len(query)}, Top-K: {top_k}")

        try:
            # 6. Tokenize the query using the configured active tokenizer
            tokenize_func = self.index_service.get_tokenizer()
            tokenized_query = tokenize_func(query)
            
            # Calculate BM25 scores
            scores = self.index_service.bm25.get_scores(tokenized_query)

            # 7. Rank matches and filter out non-matching chunks (score <= 0)
            matching_indices = [i for i in range(len(scores)) if scores[i] > 0]
            top_indices = sorted(matching_indices, key=lambda i: scores[i], reverse=True)[:top_k]

            formatted_results = []
            for rank_idx, idx in enumerate(top_indices):
                chunk = self.index_service._chunks[idx]
                doc_id = chunk.get("document_id", "Unknown")
                doc_name = self.index_service.lookup_document_name(doc_id)

                formatted_results.append(
                    RetrievalResult(
                        rank=rank_idx + 1,
                        score=float(scores[idx]),
                        retrieval_type="bm25",
                        document_id=doc_id,
                        document_name=doc_name,
                        page_number=chunk.get("page_number", 0),
                        chunk_id=chunk.get("chunk_id", "Unknown"),
                        text=chunk.get("text", "")
                    )
                )

            elapsed_time = time.time() - start_time
            logger.info(
                f"Completed BM25 search in {elapsed_time:.4f} seconds. "
                f"Found {len(formatted_results)} matching chunks."
            )
            return formatted_results

        except Exception as e:
            logger.exception("Unexpected error during BM25 search processing")
            return []

    def get_stats(self) -> dict:
        """Returns statistics about the underlying BM25 index."""
        return self.index_service.get_index_stats()

    def health_check(self) -> bool:
        """Returns if the BM25 index service is healthy."""
        return self.index_service.health_check()
