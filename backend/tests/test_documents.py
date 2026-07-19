import sys
import os
import unittest
import json
from unittest.mock import patch, MagicMock

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app

class TestDocumentsBlueprint(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_get_document_chunks_invalid_uuid(self):
        """Verify that invalid UUID formats return a 400 Bad Request."""
        # Traversal payload
        response = self.client.get("/api/documents/../../etc/passwd/chunks")
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertIn("Invalid document ID format", data["message"])

        # Non-UUID format
        response = self.client.get("/api/documents/non-uuid-string/chunks")
        self.assertEqual(response.status_code, 400)

    def test_delete_document_invalid_uuid(self):
        """Verify that invalid UUID formats return a 400 Bad Request on DELETE."""
        response = self.client.delete("/api/documents/non-uuid-string")
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertIn("Invalid document ID format", data["message"])

    @patch("app.routes.documents.os.path.exists")
    def test_delete_document_not_found(self, mock_exists):
        """Verify deleting a non-existent document ID returns a 404."""
        mock_exists.return_value = False
        valid_uuid = "06d5ec23-131e-4fd5-8f7b-002491bbe226"
        response = self.client.delete(f"/api/documents/{valid_uuid}")
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertIn("not found", data["message"])

    @patch("app.routes.documents.os.path.exists")
    @patch("app.routes.documents.open")
    @patch("app.routes.documents.json.load")
    @patch("app.routes.documents.os.remove")
    @patch("app.routes.documents.get_vector_index_service")
    def test_delete_document_success(self, mock_get_index_service, mock_remove, mock_json_load, mock_open, mock_exists):
        """Verify successful document deletion flow and index rebuild trigger."""
        # Mock file existence checks
        # meta_path, extracted_path, processed_path, chunks_path, npy_path, npy_meta_path, raw_path
        mock_exists.side_effect = lambda p: True
        
        # Mock JSON loader return values for metadata read
        mock_json_load.return_value = {
            "document_id": "06d5ec23-131e-4fd5-8f7b-002491bbe226",
            "filename": "06d5ec23-131e-4fd5-8f7b-002491bbe226_dummy.pdf"
        }
        
        # Mock index service rebuild
        mock_index_service = MagicMock()
        mock_get_index_service.return_value = mock_index_service

        valid_uuid = "06d5ec23-131e-4fd5-8f7b-002491bbe226"
        response = self.client.delete(f"/api/documents/{valid_uuid}")
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIn("Successfully deleted document", data["message"])
        
        # Assert file removals called (meta, raw, extracted, processed, chunks, npy, npy_meta)
        self.assertEqual(mock_remove.call_count, 7)
        
        # Assert index rebuild was triggered
        mock_index_service.rebuild_index.assert_called_once()

if __name__ == "__main__":
    unittest.main()
