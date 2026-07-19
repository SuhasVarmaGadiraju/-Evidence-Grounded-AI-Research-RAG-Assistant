import sys
import os
import unittest
import json
from unittest.mock import patch, MagicMock

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.services.bm25_retriever import BM25RetrievalService
from app.services.bm25_index import tokenize_whitespace_lower, tokenize_simple, BM25IndexService, get_bm25_index_service

class TestBM25RetrievalService(unittest.TestCase):
    def setUp(self):
        # 1. Reset singleton instances to ensure complete test isolation
        BM25IndexService._instance = None
        
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['BM25_DEFAULT_TOP_K'] = 2
        
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        # 2. Patch os.path.exists using a patcher to avoid argument injection pollution
        self.exists_patcher = patch(
            'os.path.exists', 
            side_effect=lambda p: False if "bm25_index" in p.replace("\\", "/") else True
        )
        self.mock_exists = self.exists_patcher.start()
        
        # Define mock documents metadata returned by list_ingested_documents
        self.mock_ingested_docs = [
            {
                "document_id": "doc1",
                "status": "processed",
                "total_chunks": 1,
                "upload_timestamp": "2026-07-17T00:00:00Z"
            },
            {
                "document_id": "doc2",
                "status": "processed",
                "total_chunks": 2,
                "upload_timestamp": "2026-07-17T00:00:01Z"
            }
        ]

    def tearDown(self):
        self.exists_patcher.stop()
        self.app_context.pop()
        BM25IndexService._instance = None

    def mock_open_side_effect(self, filepath, *args, **kwargs):
        # Check if opened for writing
        mode = args[0] if len(args) > 0 else kwargs.get("mode", "r")
        if "w" in mode:
            mock_file = MagicMock()
            mock_file.__enter__.return_value = mock_file
            return mock_file

        content = ""
        normalized_path = filepath.replace("\\", "/")
        if "doc1_chunks.json" in normalized_path:
            content = json.dumps([
                {
                    "chunk_id": "doc1_p1_c0",
                    "document_id": "doc1",
                    "page_number": 1,
                    "text": "The quick brown fox jumps over the lazy dog.",
                    "strategy": "fixed"
                }
            ])
        elif "doc2_chunks.json" in normalized_path:
            content = json.dumps([
                {
                    "chunk_id": "doc2_p1_c0",
                    "document_id": "doc2",
                    "page_number": 2,
                    "text": "Python is a high-level general-purpose programming language.",
                    "strategy": "fixed"
                },
                {
                    "chunk_id": "doc2_p1_c1",
                    "document_id": "doc2",
                    "page_number": 3,
                    "text": "Artificial intelligence and machine learning are transforming research.",
                    "strategy": "fixed"
                }
            ])
        elif "_meta.json" in normalized_path:
            doc_id = os.path.basename(normalized_path).replace("_meta.json", "")
            content = json.dumps({
                "document_id": doc_id,
                "original_filename": f"SampleDocument_{doc_id}.pdf"
            })
        else:
            raise FileNotFoundError(f"File not found in mock: {filepath}")
            
        mock_file = MagicMock()
        mock_file.read.return_value = content
        mock_file.__enter__.return_value = mock_file
        return mock_file

    def test_tokenizer_variants(self):
        """Verify tokenization methods output correctly."""
        text = "The quick, brown fox! 123"
        
        # Test whitespace lower tokenizer (refined to preserve technical internal punctuation)
        tokens_wl = tokenize_whitespace_lower(text)
        self.assertEqual(tokens_wl, ["the", "quick", "brown", "fox", "123"])
        
        # Test simple tokenizer
        tokens_sim = tokenize_simple(text)
        self.assertEqual(tokens_sim, ["the", "quick", "brown", "fox", "123"])

        # Test empty input handling
        self.assertEqual(tokenize_whitespace_lower(""), [])
        self.assertEqual(tokenize_simple(None), [])

    @patch('app.services.ingest.list_ingested_documents')
    @patch('builtins.open')
    def test_exact_keyword_retrieval(self, mock_open_func, mock_list_docs):
        """Verify that exact keyword search retrieves only the relevant chunks."""
        mock_list_docs.return_value = self.mock_ingested_docs
        mock_open_func.side_effect = self.mock_open_side_effect
        
        service = BM25RetrievalService()
        results = service.search("Python")
        
        # Should match python chunk only
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].document_id, "doc2")
        self.assertEqual(results[0].chunk_id, "doc2_p1_c0")
        self.assertEqual(results[0].page_number, 2)
        self.assertIn("Python is a high-level", results[0].text)
        self.assertTrue(results[0].score > 0)
        self.assertEqual(results[0].retrieval_type, "bm25")

    @patch('app.services.ingest.list_ingested_documents')
    @patch('builtins.open')
    def test_rare_term_retrieval(self, mock_open_func, mock_list_docs):
        """Verify that rare terms yield matching results correctly."""
        mock_list_docs.return_value = self.mock_ingested_docs
        mock_open_func.side_effect = self.mock_open_side_effect
        
        service = BM25RetrievalService()
        results = service.search("transforming")
        
        # Should match machine learning chunk only
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].chunk_id, "doc2_p1_c1")
        self.assertEqual(results[0].page_number, 3)
        self.assertIn("transforming research", results[0].text)

    @patch('app.services.ingest.list_ingested_documents')
    @patch('builtins.open')
    def test_empty_corpus(self, mock_open_func, mock_list_docs):
        """Verify searching an empty corpus returns empty list gracefully."""
        mock_list_docs.return_value = []
        mock_open_func.side_effect = self.mock_open_side_effect
        
        service = BM25RetrievalService()
        results = service.search("Python")
        self.assertEqual(results, [])

    @patch('app.services.ingest.list_ingested_documents')
    @patch('builtins.open')
    def test_empty_query(self, mock_open_func, mock_list_docs):
        """Verify searching with empty or whitespace queries returns empty list."""
        mock_list_docs.return_value = self.mock_ingested_docs
        mock_open_func.side_effect = self.mock_open_side_effect
        
        service = BM25RetrievalService()
        
        self.assertEqual(service.search(""), [])
        self.assertEqual(service.search("    "), [])
        self.assertEqual(service.search(None), [])

    @patch('app.services.ingest.list_ingested_documents')
    @patch('builtins.open')
    def test_invalid_top_k(self, mock_open_func, mock_list_docs):
        """Verify invalid top_k inputs fall back to default settings."""
        mock_list_docs.return_value = self.mock_ingested_docs
        mock_open_func.side_effect = self.mock_open_side_effect
        
        service = BM25RetrievalService()
        
        # top_k=-5 should fallback to default (which is 2 in setUp)
        results = service.search("quick Python machine", top_k=-5)
        self.assertEqual(len(results), 2)
        
        # top_k=0 should fallback to default
        results = service.search("quick Python machine", top_k=0)
        self.assertEqual(len(results), 2)

    @patch('app.services.ingest.list_ingested_documents')
    @patch('builtins.open')
    def test_ranking_and_sorting(self, mock_open_func, mock_list_docs):
        """Verify results are returned in correct descending score ordering."""
        mock_list_docs.return_value = self.mock_ingested_docs
        mock_open_func.side_effect = self.mock_open_side_effect
        
        service = BM25RetrievalService()
        # Searching for terms from multiple documents
        results = service.search("quick Python dog", top_k=3)
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].rank, 1)
        self.assertEqual(results[1].rank, 2)
        
        # First result should be quick brown fox (contains 'quick', 'dog')
        self.assertEqual(results[0].document_id, "doc1")
        # Second result should be Python (contains 'Python')
        self.assertEqual(results[1].document_id, "doc2")
        
        # Verify scores are sorted descending
        self.assertTrue(results[0].score >= results[1].score)

    @patch('app.services.ingest.list_ingested_documents')
    @patch('builtins.open')
    def test_metadata_mapping(self, mock_open_func, mock_list_docs):
        """Verify returned documents map correct metadata attributes."""
        mock_list_docs.return_value = self.mock_ingested_docs
        mock_open_func.side_effect = self.mock_open_side_effect
        
        service = BM25RetrievalService()
        results = service.search("jumps", top_k=1)
        
        self.assertEqual(len(results), 1)
        res = results[0]
        self.assertEqual(res.document_id, "doc1")
        self.assertEqual(res.document_name, "SampleDocument_doc1.pdf")
        self.assertEqual(res.page_number, 1)
        self.assertEqual(res.chunk_id, "doc1_p1_c0")
        self.assertEqual(res.text, "The quick brown fox jumps over the lazy dog.")

    @patch('app.services.ingest.list_ingested_documents')
    @patch('builtins.open')
    def test_rest_api_endpoint(self, mock_open_func, mock_list_docs):
        """Verify REST API endpoint POST /api/retrieval/bm25 returns results correctly."""
        mock_list_docs.return_value = self.mock_ingested_docs
        mock_open_func.side_effect = self.mock_open_side_effect
        
        # Check success response
        response = self.client.post(
            "/api/retrieval/bm25",
            json={"query": "fox", "top_k": 1}
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["query"], "fox")
        self.assertEqual(data["top_k"], 1)
        self.assertIn("retrieval_time_seconds", data)
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["document_id"], "doc1")
        self.assertEqual(data["results"][0]["retrieval_type"], "bm25")
        
        # Check validation failure when query is missing
        response_fail = self.client.post(
            "/api/retrieval/bm25",
            json={"top_k": 5}
        )
        self.assertEqual(response_fail.status_code, 400)
        data_fail = response_fail.get_json()
        self.assertFalse(data_fail["success"])
        self.assertIn("Missing 'query' parameter", data_fail["message"])

    def test_technical_keywords_tokenization(self):
        """Verify tokenization preserves technical identifiers (snake_case, version, IP)."""
        text = "Check database logs for 192.168.1.1, connection_error, and version v1.2.3."
        tokens = tokenize_whitespace_lower(text)
        self.assertIn("192.168.1.1", tokens)
        self.assertIn("connection_error", tokens)
        self.assertIn("v1.2.3", tokens)

    @patch('app.services.ingest.list_ingested_documents')
    @patch('builtins.open')
    def test_query_limits(self, mock_open_func, mock_list_docs):
        """Verify queries exceeding limit are truncated."""
        mock_list_docs.return_value = self.mock_ingested_docs
        mock_open_func.side_effect = self.mock_open_side_effect
        
        self.app.config['BM25_MAX_QUERY_LENGTH'] = 6
        service = BM25RetrievalService()
        
        # Query longer than 6 chars should be truncated to 6 chars ("Python programming" -> "Python")
        # "Python" matches chunk containing Python.
        results = service.search("Python programming")
        self.assertEqual(len(results), 1)

    @patch('app.services.ingest.list_ingested_documents')
    @patch('builtins.open')
    def test_unknown_and_unicode_keywords(self, mock_open_func, mock_list_docs):
        """Verify unknown keywords return empty results, and unicode queries work."""
        mock_list_docs.return_value = self.mock_ingested_docs
        mock_open_func.side_effect = self.mock_open_side_effect
        
        service = BM25RetrievalService()
        self.assertEqual(service.search("completelyunknownword"), [])
        self.assertEqual(service.search("🚀"), [])

    @patch('app.services.ingest.list_ingested_documents')
    @patch('builtins.open')
    def test_concurrency(self, mock_open_func, mock_list_docs):
        """Verify concurrent search and check_and_sync operations do not cause race conditions."""
        mock_list_docs.return_value = self.mock_ingested_docs
        mock_open_func.side_effect = self.mock_open_side_effect
        
        index_service = get_bm25_index_service()
        retrieval_service = BM25RetrievalService()
        
        import threading
        errors = []
        
        def run_searches():
            try:
                for _ in range(50):
                    res = retrieval_service.search("Python")
                    self.assertTrue(len(res) > 0)
            except Exception as e:
                errors.append(e)
                
        def run_syncs():
            try:
                for _ in range(20):
                    index_service.check_and_sync_index()
            except Exception as e:
                errors.append(e)
                
        threads = [
            threading.Thread(target=run_searches),
            threading.Thread(target=run_syncs),
            threading.Thread(target=run_searches),
            threading.Thread(target=run_syncs)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
            
        self.assertEqual(errors, [])

    @patch('app.services.ingest.list_ingested_documents')
    def test_index_disk_serialization(self, mock_list_docs):
        """Verify the index is correctly saved to and loaded from disk."""
        # Stop exists patcher to use actual disk path checks during this serialization test
        self.exists_patcher.stop()
        
        import tempfile
        import shutil
        temp_dir = tempfile.mkdtemp()
        
        mock_chunks = [
            {"chunk_id": "c1", "document_id": "d1", "page_number": 1, "text": "Vite React tailwind"}
        ]
        
        try:
            with patch('app.services.bm25_index.INDEX_DIR', temp_dir):
                with patch('app.services.bm25_index.CHUNKS_DIR', temp_dir):
                    chunk_file = os.path.join(temp_dir, "d1_chunks.json")
                    with open(chunk_file, "w", encoding="utf-8") as f:
                        json.dump(mock_chunks, f)
                        
                    mock_list_docs.return_value = [
                        {"document_id": "d1", "status": "processed", "total_chunks": 1, "upload_timestamp": "timestamp"}
                    ]
                    
                    # Reset singleton for testing
                    BM25IndexService._instance = None
                    index_service = BM25IndexService()
                    index_service.check_and_sync_index()
                    
                    pkl_path = os.path.join(temp_dir, "bm25_index.pkl")
                    mapping_path = os.path.join(temp_dir, "bm25_index_mapping.json")
                    meta_path = os.path.join(temp_dir, "bm25_index_meta.json")
                    
                    self.assertTrue(os.path.exists(pkl_path))
                    self.assertTrue(os.path.exists(mapping_path))
                    self.assertTrue(os.path.exists(meta_path))
                    
                    # Verify loading
                    BM25IndexService._instance = None
                    new_service = BM25IndexService()
                    self.assertEqual(len(new_service._chunks), 1)
                    self.assertEqual(new_service._chunks[0]["text"], "Vite React tailwind")
        finally:
            shutil.rmtree(temp_dir)
            # Re-start patcher to maintain state for potential teardown calls
            self.exists_patcher.start()

if __name__ == "__main__":
    unittest.main()
