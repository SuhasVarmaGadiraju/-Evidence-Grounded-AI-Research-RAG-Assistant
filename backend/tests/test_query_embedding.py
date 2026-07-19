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
from app.services.query_embedding import QueryEmbeddingService, QueryEmbeddingError

class TestQueryEmbeddingService(unittest.TestCase):
    def setUp(self):
        # Reset EmbeddingService singletons
        EmbeddingService._instance = None
        EmbeddingService._model = None
        self.service = QueryEmbeddingService()
        
        # Flask application instance for endpoint testing
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def tearDown(self):
        EmbeddingService._instance = None
        EmbeddingService._model = None

    def test_query_dimension_and_type(self):
        """Verify generated embedding dimension size and datatype."""
        query = "What are semantic chunks?"
        emb = self.service.generate_query_embedding(query)
        
        self.assertIsInstance(emb, np.ndarray)
        self.assertEqual(emb.dtype, np.float32)
        self.assertEqual(emb.shape, (384,))
        
        # Verify L2 normalized (norm is close to 1.0)
        norm = np.linalg.norm(emb)
        self.assertAlmostEqual(norm, 1.0, places=5)

    def test_empty_and_whitespace_query_validation(self):
        """Verify raising QueryEmbeddingError on empty or whitespace strings."""
        with self.assertRaises(QueryEmbeddingError) as ctx:
            self.service.generate_query_embedding("")
        self.assertIn("cannot be empty", str(ctx.exception))
        
        with self.assertRaises(QueryEmbeddingError) as ctx:
            self.service.generate_query_embedding("    ")
        self.assertIn("cannot be empty", str(ctx.exception))

    def test_excessively_long_query_validation(self):
        """Verify raising QueryEmbeddingError on query inputs > 1000 characters."""
        long_query = "A" * 1001
        with self.assertRaises(QueryEmbeddingError) as ctx:
            self.service.generate_query_embedding(long_query)
        self.assertIn("too long", str(ctx.exception))

    def test_multilingual_query_input(self):
        """Verify embedding generation on non-English queries."""
        hindi_query = "डेटाबेस क्या है?"
        french_query = "Qu'est-ce qu'une base de données ?"
        
        emb_hindi = self.service.generate_query_embedding(hindi_query)
        emb_french = self.service.generate_query_embedding(french_query)
        
        self.assertEqual(emb_hindi.shape, (384,))
        self.assertEqual(emb_french.shape, (384,))
        
        # Verify they are unit vectors
        self.assertAlmostEqual(np.linalg.norm(emb_hindi), 1.0, places=5)
        self.assertAlmostEqual(np.linalg.norm(emb_french), 1.0, places=5)

    def test_embedding_consistency_for_identical_queries(self):
        """Verify duplicate calls with identical queries return the same vector coordinates."""
        query = "Evidence-grounded RAG retrieval pipelines."
        emb1 = self.service.generate_query_embedding(query)
        emb2 = self.service.generate_query_embedding(query)
        
        np.testing.assert_array_almost_equal(emb1, emb2, decimal=5)

    def test_api_query_embed_endpoint_success(self):
        """Verify POST /api/query/embed success payload schema (excludes vectors)."""
        response = self.client.post(
            "/api/query/embed",
            json={"query": "Test search pipeline query."}
        )
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["query_length"], len("Test search pipeline query."))
        self.assertEqual(data["embedding_dimension"], 384)
        self.assertIn("processing_time_seconds", data)
        self.assertIn("message", data)
        
        # Vector data should NOT be present in response
        self.assertNotIn("embedding", data)
        self.assertNotIn("vector", data)

    def test_api_query_embed_endpoint_validation_errors(self):
        """Verify POST /api/query/embed error payloads on validation failure."""
        # Empty query
        res_empty = self.client.post("/api/query/embed", json={"query": "   "})
        self.assertEqual(res_empty.status_code, 400)
        self.assertFalse(res_empty.get_json()["success"])
        
        # Too long query
        res_long = self.client.post("/api/query/embed", json={"query": "A" * 1005})
        self.assertEqual(res_long.status_code, 400)
        self.assertFalse(res_long.get_json()["success"])
        
        # Missing parameter
        res_missing = self.client.post("/api/query/embed", json={})
        self.assertEqual(res_missing.status_code, 400)
        self.assertFalse(res_missing.get_json()["success"])

if __name__ == "__main__":
    unittest.main()
