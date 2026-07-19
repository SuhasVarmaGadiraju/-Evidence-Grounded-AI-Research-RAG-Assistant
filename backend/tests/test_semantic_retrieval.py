import sys
import os
import unittest
import json
import numpy as np
from unittest.mock import patch, MagicMock

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.services.embedding import EmbeddingService
from app.services.vector_index import FAISSIndexService
from app.services.semantic_retrieval import SemanticRetrievalService, SemanticRetrievalError

class TestSemanticRetrievalService(unittest.TestCase):
    def setUp(self):
        # Reset services
        EmbeddingService._instance = None
        EmbeddingService._model = None
        FAISSIndexService._instance = None
        
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.service = SemanticRetrievalService()

    def tearDown(self):
        # Reset singletons
        EmbeddingService._instance = None
        EmbeddingService._model = None
        FAISSIndexService._instance = None

    def test_empty_query_returns_empty_results(self):
        """Verify that empty/whitespace queries return an empty list gracefully."""
        res_empty = self.service.retrieve("")
        self.assertEqual(res_empty, [])
        
        res_whitespace = self.service.retrieve("   ")
        self.assertEqual(res_whitespace, [])

    def test_semantic_ranking_and_score_sorting(self):
        """Verify that returned results are ranked and sorted in descending score order."""
        # Mock index service search to return predefined matches with custom scores
        mock_matches = [
            {"chunk_id": "c1", "document_id": "d1", "text": "high match", "page_number": 2, "score": 0.95},
            {"chunk_id": "c2", "document_id": "d1", "text": "med match", "page_number": 4, "score": 0.72},
            {"chunk_id": "c3", "document_id": "d2", "text": "low match", "page_number": 1, "score": 0.31}
        ]
        
        with patch.object(self.service.vector_index_service, 'search', return_value=mock_matches):
            with patch.object(self.service, '_lookup_document_name', return_value="Test Doc"):
                results = self.service.retrieve("What is ranking?", top_k=3)
                
                self.assertEqual(len(results), 3)
                
                # Check ranks
                self.assertEqual(results[0]["rank"], 1)
                self.assertEqual(results[1]["rank"], 2)
                self.assertEqual(results[2]["rank"], 3)
                
                # Check scores descending
                self.assertEqual(results[0]["similarity_score"], 0.95)
                self.assertEqual(results[1]["similarity_score"], 0.72)
                self.assertEqual(results[2]["similarity_score"], 0.31)
                
                # Verify document details mapped correctly
                self.assertEqual(results[0]["document_id"], "d1")
                self.assertEqual(results[0]["document_name"], "Test Doc")
                self.assertEqual(results[0]["page_number"], 2)
                self.assertEqual(results[0]["chunk_id"], "c1")
                self.assertEqual(results[0]["text"], "high match")

    def test_configurable_top_k_behavior(self):
        """Verify that the retrieve method respects configurable top_k values."""
        # Create a mock list of 10 items
        mock_matches = [{"chunk_id": f"c{i}", "document_id": "d1", "text": f"text {i}", "page_number": 1, "score": 0.5} for i in range(10)]
        
        # Helper check to ensure FAISS search is called with the resolved top_k value
        def mock_search(query_vector, k):
            return mock_matches[:k]
            
        with patch.object(self.service.vector_index_service, 'search', side_effect=mock_search):
            with patch.object(self.service, '_lookup_document_name', return_value="Test Doc"):
                # Case 1: Custom top_k = 3
                res_3 = self.service.retrieve("query text", top_k=3)
                self.assertEqual(len(res_3), 3)
                
                # Case 2: Custom top_k = 8
                res_8 = self.service.retrieve("query text", top_k=8)
                self.assertEqual(len(res_8), 8)
                
                # Case 3: Invalid top_k falls back to DEFAULT_TOP_K (which is 5)
                res_invalid = self.service.retrieve("query text", top_k=-1)
                self.assertEqual(len(res_invalid), 5)

    def test_empty_index_returns_empty_results(self):
        """Verify that searching on an uninitialized/empty index returns empty list."""
        with patch.object(self.service.vector_index_service, 'search', return_value=[]):
            results = self.service.retrieve("query text")
            self.assertEqual(results, [])

    @patch('app.services.semantic_retrieval.logger')
    def test_retrieval_latency_logging(self, mock_logger):
        """Verify that search latency and completion metrics are logged."""
        mock_matches = [
            {"chunk_id": "c1", "document_id": "d1", "text": "matched text", "page_number": 1, "score": 0.85}
        ]
        with patch.object(self.service.vector_index_service, 'search', return_value=mock_matches):
            with patch.object(self.service, '_lookup_document_name', return_value="Test Doc"):
                self.service.retrieve("query text")
                
                # Confirm logger.info was called with latency statements
                latency_log_found = False
                for call in mock_logger.info.call_args_list:
                    log_msg = call[0][0]
                    if "Completed semantic search in" in log_msg:
                        latency_log_found = True
                        break
                self.assertTrue(latency_log_found, "Latency execution statement not logged.")

    def test_api_retrieval_search_endpoint_success(self):
        """Verify POST /api/retrieval/search endpoint response structure and latency metrics."""
        mock_matches = [
            {"chunk_id": "c1", "document_id": "d1", "text": "matched text", "page_number": 2, "score": 0.88}
        ]
        
        with patch.object(SemanticRetrievalService, 'retrieve', return_value=[
            {
                "rank": 1,
                "similarity_score": 0.88,
                "document_id": "d1",
                "document_name": "filename.pdf",
                "page_number": 2,
                "chunk_id": "c1",
                "text": "matched text"
            }
        ]):
            response = self.client.post(
                "/api/retrieval/search",
                json={"query": "RAG search", "top_k": 3}
            )
            self.assertEqual(response.status_code, 200)
            
            data = response.get_json()
            self.assertTrue(data["success"])
            self.assertEqual(data["query"], "RAG search")
            self.assertEqual(data["top_k"], 3)
            self.assertIn("retrieval_time_seconds", data)
            
            results = data["results"]
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["rank"], 1)
            self.assertEqual(results[0]["similarity_score"], 0.88)
            self.assertEqual(results[0]["document_name"], "filename.pdf")
            self.assertEqual(results[0]["text"], "matched text")

if __name__ == "__main__":
    unittest.main()
