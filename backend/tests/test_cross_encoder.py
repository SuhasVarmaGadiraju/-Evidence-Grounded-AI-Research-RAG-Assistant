import sys
import os
import unittest
import json
from unittest.mock import patch, MagicMock

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.services.base_retriever import RetrievalResult
from app.services.cross_encoder import CrossEncoderService

class TestCrossEncoderService(unittest.TestCase):
    def setUp(self):
        # 1. Reset singleton instances to ensure complete test isolation
        CrossEncoderService._instance = None
        CrossEncoderService._model = None
        
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['RERANK_MODEL'] = "mock-cross-encoder"
        self.app.config['RERANK_TOP_K'] = 2
        self.app.config['RERANK_BATCH_SIZE'] = 4
        
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

    def tearDown(self):
        self.app_context.pop()
        CrossEncoderService._instance = None
        CrossEncoderService._model = None

    @patch('app.services.cross_encoder.CrossEncoder')
    def test_singleton_model_loading(self, mock_cross_encoder_class):
        """Verify that the model is loaded lazily and only once as a singleton."""
        mock_model = MagicMock()
        mock_cross_encoder_class.return_value = mock_model
        
        service1 = CrossEncoderService()
        service2 = CrossEncoderService()
        
        # Verify they are the same instance (singleton service)
        self.assertIs(service1, service2)
        
        # Verify model has not loaded until get_model is called
        mock_cross_encoder_class.assert_not_called()
        
        model1 = service1.get_model()
        model2 = service2.get_model()
        
        # Verify model is the same instance
        self.assertIs(model1, model2)
        
        # Verify CrossEncoder was only instantiated once
        mock_cross_encoder_class.assert_called_once_with("mock-cross-encoder")

    @patch('app.services.cross_encoder.CrossEncoder')
    def test_reranking_correctness_and_ordering(self, mock_cross_encoder_class):
        """Verify candidate list is correctly scored and sorted descending."""
        mock_model = MagicMock()
        # Mock scores returned for candidates (e.g. chunk1, chunk2, chunk3)
        mock_model.predict.return_value = [0.15, 0.85, 0.45]
        mock_cross_encoder_class.return_value = mock_model
        
        candidates = [
            RetrievalResult(1, 0.9, "hybrid", "d1", "doc.pdf", 1, "chunk1", "text 1", "both"),
            RetrievalResult(2, 0.8, "hybrid", "d1", "doc.pdf", 2, "chunk2", "text 2", "semantic"),
            RetrievalResult(3, 0.75, "hybrid", "d2", "doc.pdf", 1, "chunk3", "text 3", "bm25")
        ]
        
        service = CrossEncoderService()
        results = service.rerank("query text", candidates, top_k=3)
        
        self.assertEqual(len(results), 3)
        
        # Expected scores and sort order:
        # chunk2: 0.85 (rank 1)
        # chunk3: 0.45 (rank 2)
        # chunk1: 0.15 (rank 3)
        self.assertEqual(results[0].chunk_id, "chunk2")
        self.assertEqual(results[0].rank, 1)
        self.assertAlmostEqual(results[0].rerank_score, 0.85)

        self.assertEqual(results[1].chunk_id, "chunk3")
        self.assertEqual(results[1].rank, 2)
        self.assertAlmostEqual(results[1].rerank_score, 0.45)

        self.assertEqual(results[2].chunk_id, "chunk1")
        self.assertEqual(results[2].rank, 3)
        self.assertAlmostEqual(results[2].rerank_score, 0.15)

    @patch('app.services.cross_encoder.CrossEncoder')
    def test_empty_candidates_and_queries(self, mock_cross_encoder_class):
        """Verify empty conditions return empty lists gracefully."""
        service = CrossEncoderService()
        
        # Empty query
        self.assertEqual(service.rerank("", [MagicMock()]), [])
        self.assertEqual(service.rerank(None, [MagicMock()]), [])
        
        # Empty candidates list
        self.assertEqual(service.rerank("query", []), [])
        self.assertEqual(service.rerank("query", None), [])

    @patch('app.services.cross_encoder.CrossEncoder')
    def test_stable_reranking_ties(self, mock_cross_encoder_class):
        """Verify stable ranking alphabetical tie-breaker works when rerank scores are equal."""
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.5, 0.5]
        mock_cross_encoder_class.return_value = mock_model
        
        candidates = [
            RetrievalResult(1, 0.9, "hybrid", "d1", "doc.pdf", 1, "chunkB", "text B", "both"),
            RetrievalResult(2, 0.8, "hybrid", "d1", "doc.pdf", 2, "chunkA", "text A", "both")
        ]
        
        service = CrossEncoderService()
        results = service.rerank("query", candidates)
        
        self.assertEqual(len(results), 2)
        # Alphabetical tie-breaking: chunkA should rank 1, chunkB should rank 2
        self.assertEqual(results[0].chunk_id, "chunkA")
        self.assertEqual(results[1].chunk_id, "chunkB")

    @patch('app.services.cross_encoder.CrossEncoder')
    def test_large_top_k(self, mock_cross_encoder_class):
        """Verify requesting top_k larger than candidates slice lists safely."""
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.9]
        mock_cross_encoder_class.return_value = mock_model
        
        candidates = [
            RetrievalResult(1, 0.9, "hybrid", "d1", "doc.pdf", 1, "chunk1", "text 1", "both")
        ]
        
        service = CrossEncoderService()
        results = service.rerank("query", candidates, top_k=50)
        self.assertEqual(len(results), 1)

    @patch('app.services.hybrid_retriever.HybridRetrievalService.search')
    @patch('app.services.cross_encoder.CrossEncoder')
    def test_rest_api_rerank_endpoint(self, mock_cross_encoder_class, mock_hybrid_search):
        """Verify REST API POST /api/retrieval/rerank returns correct payload structures."""
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.95]
        mock_cross_encoder_class.return_value = mock_model
        
        mock_hybrid_search.return_value = [
            RetrievalResult(1, 0.03, "hybrid", "d1", "doc.pdf", 1, "chunk1", "text 1", "both")
        ]
        
        response = self.client.post(
            "/api/retrieval/rerank",
            json={"query": "Rerank search test", "top_k": 1}
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["query"], "Rerank search test")
        self.assertEqual(data["top_k"], 1)
        self.assertIn("retrieval_time_seconds", data)
        self.assertIn("rerank_time_seconds", data)
        self.assertIn("hybrid_retrieval_time_seconds", data)
        
        results = data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["rank"], 1)
        self.assertEqual(results[0]["retrieval_type"], "hybrid")
        self.assertEqual(results[0]["match_source"], "both")
        self.assertAlmostEqual(results[0]["rerank_score"], 0.95)
        
        # Check error response
        response_fail = self.client.post(
            "/api/retrieval/rerank",
            json={"top_k": 2}
        )
        self.assertEqual(response_fail.status_code, 400)
        data_fail = response_fail.get_json()
        self.assertFalse(data_fail["success"])
        self.assertIn("Missing 'query' parameter", data_fail["message"])

if __name__ == "__main__":
    unittest.main()
