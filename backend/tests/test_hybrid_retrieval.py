import sys
import os
import unittest
import json
from unittest.mock import patch, MagicMock

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.services.base_retriever import RetrievalResult
from app.services.hybrid_retriever import HybridRetrievalService

class TestHybridRetrievalService(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['HYBRID_RRF_K'] = 60
        self.app.config['HYBRID_DEFAULT_TOP_K'] = 3
        
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        self.service = HybridRetrievalService()

    def tearDown(self):
        self.app_context.pop()

    @patch('app.services.semantic_retrieval.SemanticRetrievalService.search')
    @patch('app.services.bm25_retriever.BM25RetrievalService.search')
    def test_rrf_correctness_and_duplicate_merging(self, mock_bm25_search, mock_semantic_search):
        """Verify RRF scores sum correctly for duplicates and match_source resolves to 'both'."""
        # Chunk 1: Semantic Rank 1, BM25 Rank 2
        # Chunk 2: Semantic Rank 2, BM25 none
        # Chunk 3: Semantic none, BM25 Rank 1
        
        mock_semantic_search.return_value = [
            RetrievalResult(1, 0.9, "semantic", "d1", "doc.pdf", 1, "chunk1", "text 1"),
            RetrievalResult(2, 0.8, "semantic", "d1", "doc.pdf", 2, "chunk2", "text 2")
        ]
        mock_bm25_search.return_value = [
            RetrievalResult(1, 4.5, "bm25", "d2", "doc.pdf", 1, "chunk3", "text 3"),
            RetrievalResult(2, 3.2, "bm25", "d1", "doc.pdf", 1, "chunk1", "text 1")
        ]
        
        # Expected scores (K = 60):
        # chunk1: 1/(60+1) + 1/(60+2) = 1/61 + 1/62 = 0.016393 + 0.016129 = 0.032522 (source: both)
        # chunk3: 1/(60+1) = 0.016393 (source: bm25)
        # chunk2: 1/(60+2) = 0.016129 (source: semantic)
        
        results = self.service.search("query text", top_k=3)
        
        self.assertEqual(len(results), 3)
        
        # Chunk 1 should be rank 1
        self.assertEqual(results[0].chunk_id, "chunk1")
        self.assertEqual(results[0].match_source, "both")
        self.assertAlmostEqual(results[0].score, 0.032522, places=5)
        
        # Chunk 3 should be rank 2
        self.assertEqual(results[1].chunk_id, "chunk3")
        self.assertEqual(results[1].match_source, "bm25")
        self.assertAlmostEqual(results[1].score, 0.016393, places=5)
        
        # Chunk 2 should be rank 3
        self.assertEqual(results[2].chunk_id, "chunk2")
        self.assertEqual(results[2].match_source, "semantic")
        self.assertAlmostEqual(results[2].score, 0.016129, places=5)

    @patch('app.services.semantic_retrieval.SemanticRetrievalService.search')
    @patch('app.services.bm25_retriever.BM25RetrievalService.search')
    def test_empty_semantic_results(self, mock_bm25_search, mock_semantic_search):
        """Verify behavior when semantic search yields empty results."""
        mock_semantic_search.return_value = []
        mock_bm25_search.return_value = [
            RetrievalResult(1, 4.5, "bm25", "d2", "doc.pdf", 1, "chunk3", "text 3")
        ]
        
        results = self.service.search("query text")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].chunk_id, "chunk3")
        self.assertEqual(results[0].match_source, "bm25")
        self.assertAlmostEqual(results[0].score, 1.0 / 61.0, places=5)

    @patch('app.services.semantic_retrieval.SemanticRetrievalService.search')
    @patch('app.services.bm25_retriever.BM25RetrievalService.search')
    def test_empty_bm25_results(self, mock_bm25_search, mock_semantic_search):
        """Verify behavior when BM25 search yields empty results."""
        mock_semantic_search.return_value = [
            RetrievalResult(1, 0.9, "semantic", "d1", "doc.pdf", 1, "chunk1", "text 1")
        ]
        mock_bm25_search.return_value = []
        
        results = self.service.search("query")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].chunk_id, "chunk1")
        self.assertEqual(results[0].match_source, "semantic")

    @patch('app.services.semantic_retrieval.SemanticRetrievalService.search')
    @patch('app.services.bm25_retriever.BM25RetrievalService.search')
    def test_completely_empty_results(self, mock_bm25_search, mock_semantic_search):
        """Verify behavior when both retrievers return empty results."""
        mock_semantic_search.return_value = []
        mock_bm25_search.return_value = []
        
        results = self.service.search("query")
        self.assertEqual(results, [])

    def test_empty_query(self):
        """Verify that empty/whitespace queries return empty results immediately."""
        self.assertEqual(self.service.search(""), [])
        self.assertEqual(self.service.search("   "), [])
        self.assertEqual(self.service.search(None), [])

    @patch('app.services.semantic_retrieval.SemanticRetrievalService.search')
    @patch('app.services.bm25_retriever.BM25RetrievalService.search')
    def test_stable_ranking_ties(self, mock_bm25_search, mock_semantic_search):
        """Verify stable ranking on ties. Break ties by chunk_id alphabetically."""
        # Chunk B: Semantic Rank 1 (1/61)
        # Chunk A: BM25 Rank 1 (1/61)
        # Both have score 1/61. Sort tie breaks alphabetically -> Chunk A then Chunk B.
        mock_semantic_search.return_value = [
            RetrievalResult(1, 0.9, "semantic", "d1", "doc.pdf", 1, "chunkB", "text B")
        ]
        mock_bm25_search.return_value = [
            RetrievalResult(1, 4.5, "bm25", "d2", "doc.pdf", 1, "chunkA", "text A")
        ]
        
        results = self.service.search("query")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].chunk_id, "chunkA")
        self.assertEqual(results[1].chunk_id, "chunkB")

    @patch('app.services.semantic_retrieval.SemanticRetrievalService.search')
    @patch('app.services.bm25_retriever.BM25RetrievalService.search')
    def test_rest_api_endpoint(self, mock_bm25_search, mock_semantic_search):
        """Verify POST /api/retrieval/hybrid route returns successful response schema."""
        mock_semantic_search.return_value = [
            RetrievalResult(1, 0.9, "semantic", "d1", "doc.pdf", 1, "chunk1", "text 1")
        ]
        mock_bm25_search.return_value = []
        
        response = self.client.post(
            "/api/retrieval/hybrid",
            json={"query": "RAG search", "top_k": 1}
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["query"], "RAG search")
        self.assertEqual(data["top_k"], 1)
        self.assertIn("retrieval_time_seconds", data)
        
        results = data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["rank"], 1)
        self.assertEqual(results[0]["retrieval_type"], "hybrid")
        self.assertEqual(results[0]["match_source"], "semantic")
        self.assertEqual(results[0]["chunk_id"], "chunk1")

        # Check validation error for missing query
        response_fail = self.client.post(
            "/api/retrieval/hybrid",
            json={"top_k": 5}
        )
        self.assertEqual(response_fail.status_code, 400)
        data_fail = response_fail.get_json()
        self.assertFalse(data_fail["success"])
        self.assertIn("Missing 'query' parameter", data_fail["message"])

if __name__ == "__main__":
    unittest.main()
