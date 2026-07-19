import sys
import os
import unittest
import json
import shutil
import numpy as np
from unittest.mock import patch, MagicMock

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.embedding import EmbeddingService, EmbeddingServiceError
from app.services.embedding_generator import (
    generate_embeddings_for_document,
    CHUNKS_DIR,
    EMBEDDINGS_DIR
)

class TestEmbeddingGenerator(unittest.TestCase):
    def setUp(self):
        # Reset the EmbeddingService singletons
        EmbeddingService._instance = None
        EmbeddingService._model = None
        
        # Setup temporary folders for testing to not corrupt actual workspace files
        self.test_doc_id = "test-uuid-12345"
        self.chunks_file = os.path.join(CHUNKS_DIR, f"{self.test_doc_id}_chunks.json")
        self.npy_file = os.path.join(EMBEDDINGS_DIR, f"{self.test_doc_id}_embeddings.npy")
        self.meta_file = os.path.join(EMBEDDINGS_DIR, f"{self.test_doc_id}_meta.json")

    def tearDown(self):
        # Clean up any generated test files
        for f in [self.chunks_file, self.npy_file, self.meta_file]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass
        # Reset singleton models
        EmbeddingService._instance = None
        EmbeddingService._model = None

    def test_document_embedding_generation_success(self):
        """Verify that every chunk has an embedding and outputs match metadata specifications."""
        # 1. Create a dummy chunks JSON file
        dummy_chunks = [
            {"chunk_id": f"{self.test_doc_id}_c0", "text": "This is chunk 1 content."},
            {"chunk_id": f"{self.test_doc_id}_c1", "text": "This is chunk 2 content."},
            {"chunk_id": f"{self.test_doc_id}_c2", "text": "This is chunk 3 content."}
        ]
        
        with open(self.chunks_file, "w", encoding="utf-8") as f:
            json.dump(dummy_chunks, f)
            
        # 2. Run the embedding generator
        res = generate_embeddings_for_document(self.test_doc_id, batch_size=2)
        
        # Verify result status
        self.assertTrue(res["success"])
        self.assertEqual(res["chunk_count"], 3)
        self.assertEqual(res["embedding_dimension"], 384)
        
        # 3. Check that the output files exist
        self.assertTrue(os.path.exists(self.npy_file))
        self.assertTrue(os.path.exists(self.meta_file))
        
        # 4. Load the numpy array and verify shape (must match chunk count and model dimension)
        embeddings_matrix = np.load(self.npy_file)
        self.assertIsInstance(embeddings_matrix, np.ndarray)
        self.assertEqual(embeddings_matrix.shape, (3, 384))
        self.assertEqual(embeddings_matrix.dtype, np.float32)
        
        # 5. Load metadata and verify fields
        with open(self.meta_file, "r", encoding="utf-8") as f:
            meta = json.load(f)
            
        self.assertEqual(meta["document_id"], self.test_doc_id)
        self.assertEqual(meta["embedding_model"], "all-MiniLM-L6-v2")
        self.assertEqual(meta["embedding_dimension"], 384)
        self.assertEqual(meta["chunk_count"], 3)
        self.assertEqual(meta["embedding_version"], "1.0")
        self.assertIn("created_timestamp", meta)

    def test_batch_embedding_sizes(self):
        """Verify generator processes chunks in correct batches and merges properly."""
        dummy_chunks = [
            {"chunk_id": f"{self.test_doc_id}_c{i}", "text": f"Content {i}."} for i in range(10)
        ]
        
        with open(self.chunks_file, "w", encoding="utf-8") as f:
            json.dump(dummy_chunks, f)
            
        # Mock embed_batch to track the actual batch size calls
        service = EmbeddingService()
        original_embed_batch = service.embed_batch
        
        call_batches = []
        def mock_embed_batch(texts):
            call_batches.append(texts)
            return original_embed_batch(texts)
            
        with patch.object(service, 'embed_batch', side_effect=mock_embed_batch):
            # Generate with batch_size 3
            res = generate_embeddings_for_document(self.test_doc_id, batch_size=3)
            
            self.assertTrue(res["success"])
            # Batch size is 3, so 10 items should be split into batches of: 3, 3, 3, 1
            self.assertEqual(len(call_batches), 4)
            self.assertEqual([len(b) for b in call_batches], [3, 3, 3, 1])
            
            # Verify total output matrix dimension
            embeddings_matrix = np.load(self.npy_file)
            self.assertEqual(embeddings_matrix.shape, (10, 384))

    def test_empty_chunks_list_handling(self):
        """Verify handling of document with zero chunks."""
        # Create empty chunks list
        with open(self.chunks_file, "w", encoding="utf-8") as f:
            json.dump([], f)
            
        res = generate_embeddings_for_document(self.test_doc_id)
        
        self.assertTrue(res["success"])
        self.assertEqual(res["chunk_count"], 0)
        
        # Output files must exist
        self.assertTrue(os.path.exists(self.npy_file))
        self.assertTrue(os.path.exists(self.meta_file))
        
        # Matrix must be of shape (0, 384)
        matrix = np.load(self.npy_file)
        self.assertEqual(matrix.shape, (0, 384))
        
        with open(self.meta_file, "r", encoding="utf-8") as f:
            meta = json.load(f)
        self.assertEqual(meta["chunk_count"], 0)

    def test_error_propagation_missing_chunks_file(self):
        """Verify raising FileNotFoundError if chunks json is missing."""
        # self.test_doc_id chunks file was not created, so it doesn't exist
        with self.assertRaises(FileNotFoundError):
            generate_embeddings_for_document(self.test_doc_id)

    def test_error_propagation_invalid_json(self):
        """Verify raising exception when chunks file content is corrupted."""
        # Write malformed json content
        with open(self.chunks_file, "w", encoding="utf-8") as f:
            f.write("{invalid_json_data...")
            
        with self.assertRaises(ValueError):
            generate_embeddings_for_document(self.test_doc_id)

    def test_error_propagation_embedding_failures(self):
        """Verify that exceptions during embedding generation propagate."""
        dummy_chunks = [
            {"chunk_id": f"{self.test_doc_id}_c0", "text": "Chunk text"}
        ]
        with open(self.chunks_file, "w", encoding="utf-8") as f:
            json.dump(dummy_chunks, f)
            
        service = EmbeddingService()
        
        # Force embed_batch to raise an exception
        with patch.object(service, 'embed_batch', side_effect=Exception("GPU out of memory")):
            with self.assertRaises(EmbeddingServiceError) as ctx:
                generate_embeddings_for_document(self.test_doc_id)
            
            self.assertIn("Embedding encoding failed", str(ctx.exception))

if __name__ == "__main__":
    unittest.main()
