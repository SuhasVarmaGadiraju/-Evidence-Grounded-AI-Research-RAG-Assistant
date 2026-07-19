import os
import time
import logging
from flask import current_app
from app.services.base_retriever import BaseRetriever, RetrievalResult
from app.services.semantic_retrieval import SemanticRetrievalService
from app.services.bm25_retriever import BM25RetrievalService
from app.config import get_config

logger = logging.getLogger("rag_backend.hybrid_retriever")

class HybridRetrievalService(BaseRetriever):
    """
    Coordinating retriever service that fuses dense Semantic search results
    and sparse BM25 search results using Reciprocal Rank Fusion (RRF).
    """
    def __init__(self):
        self.semantic_service = SemanticRetrievalService()
        self.bm25_service = BM25RetrievalService()

    def _get_rrf_k(self) -> int:
        """Resolves the Reciprocal Rank Fusion constant parameter (K) from configuration."""
        try:
            if current_app and hasattr(current_app, "config"):
                return current_app.config.get("HYBRID_RRF_K", 60)
        except (RuntimeError, ImportError):
            pass
            
        try:
            config = get_config()
            return getattr(config, "HYBRID_RRF_K", 60)
        except Exception:
            return 60

    def _get_default_top_k(self) -> int:
        """Resolves the default top_k value from configuration."""
        try:
            if current_app and hasattr(current_app, "config"):
                return current_app.config.get("HYBRID_DEFAULT_TOP_K", 5)
        except (RuntimeError, ImportError):
            pass
            
        try:
            config = get_config()
            return getattr(config, "HYBRID_DEFAULT_TOP_K", 5)
        except Exception:
            return 5

    def search(self, query: str, top_k: int = None) -> list[RetrievalResult]:
        """
        Performs hybrid retrieval by querying both semantic and BM25 retrievers,
        collapsing duplicates, and ranking them via Reciprocal Rank Fusion (RRF).
        
        Args:
            query (str): The search query.
            top_k (int, optional): The number of matches to retrieve.
            
        Returns:
            list[RetrievalResult]: Sorted list of fused search results.
        """
        start_total = time.time()

        # 1. Gracefully handle empty queries
        if not query or not query.strip():
            logger.warning("Empty search query received. Returning empty retrieval list.")
            return []

        # 2. Resolve top_k parameters
        if top_k is None or not isinstance(top_k, int) or top_k <= 0:
            if top_k is not None:
                logger.warning(f"Invalid top_k value '{top_k}' provided. Falling back to default.")
            top_k = self._get_default_top_k()

        # 3. Execute individual searches with stopwatch profiling
        start_sem = time.time()
        semantic_results = self.semantic_service.search(query, top_k=top_k)
        sem_latency = time.time() - start_sem

        start_bm = time.time()
        bm25_results = self.bm25_service.search(query, top_k=top_k)
        bm_latency = time.time() - start_bm

        # 4. Perform duplicate merging and RRF score calculation
        start_merge = time.time()
        chunk_map = {}

        # Record semantic ranks (rank is index + 1)
        for idx, res in enumerate(semantic_results):
            cid = res.chunk_id
            if cid not in chunk_map:
                chunk_map[cid] = {
                    "chunk": res,
                    "semantic_rank": idx + 1,
                    "bm25_rank": None
                }
            else:
                chunk_map[cid]["semantic_rank"] = idx + 1

        # Record BM25 ranks
        for idx, res in enumerate(bm25_results):
            cid = res.chunk_id
            if cid not in chunk_map:
                chunk_map[cid] = {
                    "chunk": res,
                    "semantic_rank": None,
                    "bm25_rank": idx + 1
                }
            else:
                chunk_map[cid]["bm25_rank"] = idx + 1

        merge_latency = time.time() - start_merge

        # 5. RRF score computation
        start_rrf = time.time()
        rrf_k = self._get_rrf_k()
        
        for item in chunk_map.values():
            rrf_score = 0.0
            sources = []
            
            if item["semantic_rank"] is not None:
                rrf_score += 1.0 / (rrf_k + item["semantic_rank"])
                sources.append("semantic")
                
            if item["bm25_rank"] is not None:
                rrf_score += 1.0 / (rrf_k + item["bm25_rank"])
                sources.append("bm25")
                
            item["rrf_score"] = rrf_score
            item["match_source"] = "both" if len(sources) == 2 else sources[0]

        # Sort with stable tie-breaking: rrf_score descending, chunk_id ascending
        sorted_items = sorted(
            chunk_map.values(),
            key=lambda x: (-x["rrf_score"], x["chunk"].chunk_id)
        )
        
        # Select Top-K and serialize
        results = []
        for rank_idx, item in enumerate(sorted_items[:top_k]):
            chunk = item["chunk"]
            results.append(
                RetrievalResult(
                    rank=rank_idx + 1,
                    score=item["rrf_score"],
                    retrieval_type="hybrid",
                    document_id=chunk.document_id,
                    document_name=chunk.document_name,
                    page_number=chunk.page_number,
                    chunk_id=chunk.chunk_id,
                    text=chunk.text,
                    match_source=item["match_source"]
                )
            )
            
        rrf_latency = time.time() - start_rrf
        total_latency = time.time() - start_total

        # Log detailed execution profile
        logger.info(
            f"Hybrid search completed in {total_latency:.4f}s. Latency profile: "
            f"semantic={sem_latency:.4f}s, bm25={bm_latency:.4f}s, "
            f"merge={merge_latency:.4f}s, rrf={rrf_latency:.4f}s. "
            f"Query length: {len(query)}, Top-K: {top_k}, matches returned: {len(results)}."
        )

        return results

    def get_stats(self) -> dict:
        """Returns statistical details of the underlying services."""
        return {
            "rrf_parameter_k": self._get_rrf_k(),
            "semantic_stats": self.semantic_service.get_stats(),
            "bm25_stats": self.bm25_service.get_stats()
        }

    def health_check(self) -> bool:
        """Verifies if both semantic and BM25 index subsystems are healthy."""
        try:
            return self.semantic_service.health_check() and self.bm25_service.health_check()
        except Exception:
            return False
