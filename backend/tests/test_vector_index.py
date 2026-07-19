import sys
import os
import unittest
import json
import numpy as np
import faiss
from unittest.mock import patch, MagicMock

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.vector_index import (
    FAISSIndexService,
    VectorIndexServiceError,
    INDEX_DIR,
    METADATA_DIR,
    EMBEDDINGS_DIR,
    CHUNKS_DIR
)
from app.services.embedding import EmbeddingService

class TestVectorIndexService(unittest.TestCase):
    def setUp(self):
        # Reset services
        FAISSIndexService._instance = None
        EmbeddingService._instance = None
        EmbeddingService._model = None
        
        # Test file paths
        self.index_file = os.path.join(INDEX_DIR, "global_index.faiss")
        self.mapping_file = os.path.join(INDEX_DIR, "global_index_mapping.json")
        self.meta_file = os.path.join(INDEX_DIR, "global_index_meta.json")

        # Backup existing files if they exist to prevent corruption of user data during tests
        self.backups = {}
        for path in [self.index_file, self.mapping_file, self.meta_file]:
            if os.path.exists(path):
                backup_path = path + ".backup"
                shutil_err = None
                try:
                    os.rename(path, backup_path)
                    self.backups[path] = backup_path
                except Exception as e:
                    pass

    def tearDown(self):
        # Clean up files created during tests
        for path in [self.index_file, self.mapping_file, self.meta_file]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass

        # Restore backups if they exist
        for path, backup_path in self.backups.items():
            if os.path.exists(backup_path):
                try:
                    os.rename(backup_path, path)
                except Exception:
                    pass
        
        # Reset services
        FAISSIndexService._instance = None
        EmbeddingService._instance = None
        EmbeddingService._model = None

    def test_index_creation_and_vector_count(self):
        """Verify vector index initialization and vector count reporting."""
        service = FAISSIndexService()
        service.create_index(dimension=128)
        
        self.assertEqual(service.dimension, 128)
        self.assertIsNotNone(service._index)
        self.assertEqual(service._index.ntotal, 0)
        self.assertEqual(len(service._mapping), 0)

    def test_add_embeddings_and_id_mapping(self):
        """Verify addition of normalized embeddings and correct index mapping."""
        service = FAISSIndexService()
        service.create_index(dimension=3)
        
        # We add 2 vectors
        embeddings = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 2.0, 0.0]
        ], dtype=np.float32)
        
        metadata = [
            {"chunk_id": "chunk_0", "document_id": "doc_1", "text": "First", "page_number": 1},
            {"chunk_id": "chunk_1", "document_id": "doc_1", "text": "Second", "page_number": 2}
        ]
        
        service.add_embeddings(embeddings, metadata)
        
        # Check count
        self.assertEqual(service._index.ntotal, 2)
        self.assertEqual(len(service._mapping), 2)
        
        # Verify L2 normalization occurred
        # Vector 2 had length 2.0, should be normalized to length 1.0
        reconstructed_vecs = np.zeros((2, 3), dtype=np.float32)
        for i in range(2):
            reconstructed_vecs[i] = service._index.reconstruct(i)
            
        self.assertAlmostEqual(np.linalg.norm(reconstructed_vecs[0]), 1.0, places=5)
        self.assertAlmostEqual(np.linalg.norm(reconstructed_vecs[1]), 1.0, places=5)
        self.assertEqual(reconstructed_vecs[1][1], 1.0) # [0, 2, 0] -> [0, 1, 0]

    def test_save_and_load_index(self):
        """Verify index and mapping database save and load persistence on disk."""
        service = FAISSIndexService()
        service.create_index(dimension=4)
        
        embeddings = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0]
        ], dtype=np.float32)
        
        metadata = [
            {"chunk_id": "c0", "document_id": "doc_1", "text": "A", "page_number": 1},
            {"chunk_id": "c1", "document_id": "doc_1", "text": "B", "page_number": 2}
        ]
        
        service.add_embeddings(embeddings, metadata)
        
        # Save index
        service.save_index()
        
        self.assertTrue(os.path.exists(self.index_file))
        self.assertTrue(os.path.exists(self.mapping_file))
        self.assertTrue(os.path.exists(self.meta_file))
        
        # Create a new service instance and load
        FAISSIndexService._instance = None
        new_service = FAISSIndexService()
        new_service.load_index()
        
        self.assertEqual(new_service.dimension, 4)
        self.assertEqual(new_service._index.ntotal, 2)
        self.assertEqual(new_service._mapping[0]["chunk_id"], "c0")
        self.assertEqual(new_service._mapping[1]["text"], "B")

    def test_nearest_neighbor_search(self):
        """Verify vector index cosine similarity search matches and ranking correctness."""
        service = FAISSIndexService()
        service.create_index(dimension=2)
        
        # Index unit vectors at 0 degrees and 90 degrees
        embeddings = np.array([
            [1.0, 0.0],  # Vector 0
            [0.0, 1.0]   # Vector 1
        ], dtype=np.float32)
        
        metadata = [
            {"chunk_id": "deg0", "document_id": "d1", "text": "0 deg", "page_number": 1},
            {"chunk_id": "deg90", "document_id": "d1", "text": "90 deg", "page_number": 1}
        ]
        service.add_embeddings(embeddings, metadata)
        
        # Search query close to 0 degrees: [0.9, 0.1]
        query = np.array([0.9, 0.1], dtype=np.float32)
        
        matches = service.search(query, k=2)
        
        self.assertEqual(len(matches), 2)
        
        # The closest match should be "deg0"
        self.assertEqual(matches[0]["chunk_id"], "deg0")
        self.assertGreater(matches[0]["score"], matches[1]["score"])
        
        # Since vectors are normalized, inner product score should match cosine similarity
        query_norm = query / np.linalg.norm(query)
        expected_score_0 = np.dot(query_norm, embeddings[0])
        self.assertAlmostEqual(matches[0]["score"], expected_score_0, places=5)

    def test_empty_and_corrupted_index_handling(self):
        """Verify statistics and fallback operations under empty or corrupt states."""
        service = FAISSIndexService()
        
        # 1. Test query on empty index
        matches = service.search(np.array([1.0, 0.0], dtype=np.float32))
        self.assertEqual(matches, [])
        
        # 2. Test statistics on empty state
        stats = service.get_index_stats()
        self.assertEqual(stats["status"], "empty")
        self.assertEqual(stats["vector_count"], 0)
        
        # 3. Test load corrupted index file
        os.makedirs(INDEX_DIR, exist_ok=True)
        with open(self.index_file, "w") as f:
            f.write("corrupted index content")
        with open(self.mapping_file, "w") as f:
            f.write("[]")
        with open(self.meta_file, "w") as f:
            f.write("{}")
            
        # Loading should fail gracefully, resetting the index states instead of raising uncaught errors
        with self.assertRaises(VectorIndexServiceError):
            service.load_index()
            
        self.assertIsNone(service._index)
        self.assertEqual(service._mapping, [])

    def test_error_handling_invalid_inputs(self):
        """Verify validation and error raising on incorrect input structures."""
        service = FAISSIndexService()
        service.create_index(3)
        
        # Mismatched lengths
        with self.assertRaises(VectorIndexServiceError):
            service.add_embeddings(
                np.zeros((2, 3), dtype=np.float32),
                [{"chunk_id": "c0"}]
            )
            
        # Invalid search size
        with self.assertRaises(VectorIndexServiceError):
            service.search(np.zeros(5, dtype=np.float32)) # size 5 vs index dimension 3

if __name__ == "__main__":
    unittest.main()
