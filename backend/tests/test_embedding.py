import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import numpy as np

# Ensure backend directory is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.embedding import EmbeddingService, EmbeddingServiceError

class TestEmbeddingService(unittest.TestCase):
    def setUp(self):
        # Reset the singleton model and instance class attributes before each test
        EmbeddingService._instance = None
        EmbeddingService._model = None

    def tearDown(self):
        # Reset again after the test
        EmbeddingService._instance = None
        EmbeddingService._model = None

    def test_singleton_behavior_and_lazy_loading(self):
        """Verify that the model is loaded lazily and only once."""
        service1 = EmbeddingService()
        
        # Before calling get_model or embedding, class-level cache _model should be None
        self.assertIsNone(EmbeddingService._model)

        # Patch SentenceTransformer to see if it is called exactly once
        with patch('app.services.embedding.SentenceTransformer') as MockTransformer:
            mock_model_instance = MagicMock()
            # Mock the method get_sentence_embedding_dimension
            mock_model_instance.get_sentence_embedding_dimension.return_value = 384
            MockTransformer.return_value = mock_model_instance
            
            # Request model for the first time
            model1 = service1.get_model()
            self.assertIsNotNone(model1)
            MockTransformer.assert_called_once()
            
            # Instantiating a second service reference
            service2 = EmbeddingService()
            model2 = service2.get_model()
            
            # The constructor should NOT have been called again
            MockTransformer.assert_called_once()
            
            # Check identity: model1 and model2 must reference the same cached model
            self.assertIs(model1, model2)

    def test_single_text_embedding_generation(self):
        """Verify single text embedding output format, dimension, and type."""
        service = EmbeddingService()
        
        # Generate embedding for a sample text
        emb = service.embed_text("Sample research paragraph for testing.")
        
        # Verify it's a numpy ndarray of float32
        self.assertIsInstance(emb, np.ndarray)
        self.assertEqual(emb.dtype, np.float32)
        
        # Verify dimension matches expected 384 for all-MiniLM-L6-v2
        dimension = service.get_dimension()
        self.assertEqual(dimension, 384)
        self.assertEqual(emb.shape, (384,))
        
        # Ensure values are not all zeros for non-empty text
        self.assertFalse(np.all(emb == 0))

    def test_empty_text_embedding(self):
        """Verify empty or whitespace-only strings return a zero vector."""
        service = EmbeddingService()
        
        emb_empty = service.embed_text("")
        emb_whitespace = service.embed_text("   ")
        
        dimension = service.get_dimension()
        
        self.assertEqual(emb_empty.shape, (dimension,))
        self.assertEqual(emb_whitespace.shape, (dimension,))
        self.assertTrue(np.all(emb_empty == 0))
        self.assertTrue(np.all(emb_whitespace == 0))

    def test_batch_embedding_generation(self):
        """Verify batch embedding output format, dimensions, and type."""
        service = EmbeddingService()
        
        texts = [
            "Document chunk number one.",
            "Another section of the evidence.",
            "Concluding query text."
        ]
        
        embs = service.embed_batch(texts)
        
        # Verify shape is (3, 384)
        self.assertIsInstance(embs, np.ndarray)
        self.assertEqual(embs.dtype, np.float32)
        self.assertEqual(embs.shape, (3, 384))
        
        # Verify empty batch behavior
        empty_embs = service.embed_batch([])
        self.assertEqual(empty_embs.shape, (0, 384))

    def test_correct_embedding_dimension(self):
        """Verify get_dimension returns correct value and handles fallback."""
        service = EmbeddingService()
        self.assertEqual(service.get_dimension(), 384)

        # Test fallback behavior when get_sentence_embedding_dimension fails
        with patch.object(service, 'get_model') as mock_get_model:
            mock_model = MagicMock()
            # Deliberately make get_sentence_embedding_dimension raise attribute error
            del mock_model.get_sentence_embedding_dimension
            
            # Mock encode to return a numpy array of custom dimension (e.g. 128)
            mock_model.encode.return_value = np.zeros(128, dtype=np.float32)
            mock_get_model.return_value = mock_model
            
            # Should fallback to encode-based dimension detection
            self.assertEqual(service.get_dimension(), 128)

    def test_error_handling_invalid_inputs(self):
        """Verify that proper exceptions are raised for invalid input types."""
        service = EmbeddingService()
        
        # Invalid single text inputs
        with self.assertRaises(EmbeddingServiceError):
            service.embed_text(None)
            
        with self.assertRaises(EmbeddingServiceError):
            service.embed_text(123)  # type: ignore
            
        # Invalid batch inputs
        with self.assertRaises(EmbeddingServiceError):
            service.embed_batch("not a list")  # type: ignore
            
        with self.assertRaises(EmbeddingServiceError):
            service.embed_batch([1, 2, "valid"])  # type: ignore

    def test_error_handling_model_load_failure(self):
        """Verify service failure propagation when the model fails to load."""
        service = EmbeddingService(model_name="non-existent-model-name")
        
        with patch('app.services.embedding.SentenceTransformer', side_effect=Exception("Model path error")):
            with self.assertRaises(EmbeddingServiceError) as ctx:
                service.get_model()
            
            self.assertIn("Failed to load embedding model", str(ctx.exception))

if __name__ == '__main__':
    unittest.main()
