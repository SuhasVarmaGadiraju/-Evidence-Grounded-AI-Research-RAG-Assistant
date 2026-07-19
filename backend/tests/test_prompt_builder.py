import sys
import os
import unittest
import hashlib
import logging
from unittest.mock import patch, MagicMock

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.services.base_retriever import RetrievalResult
from app.services.prompt_builder import (
    PromptBuilderService,
    PromptBuilderError,
    PromptValidationError,
    PromptValidator
)

class TestPromptBuilderService(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['MAX_CONTEXT_CHUNKS'] = 5
        self.app.config['MAX_CONTEXT_CHARACTERS'] = 4000
        self.app.config['PROMPT_TEMPLATE_VERSION'] = "rag_prompt_v1"
        self.app.config['PROMPT_VERSION'] = "1.0.0"
        self.app.config['PIPELINE_VERSION'] = "1.0.0"

        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

        self.service = PromptBuilderService()

        # Sample test retrieval results
        self.sample_chunks = [
            RetrievalResult(
                rank=1,
                score=0.92,
                retrieval_type="reranked",
                document_id="doc_1",
                document_name="deep_learning_paper.pdf",
                page_number=3,
                chunk_id="chunk_dl_001",
                text="Transformers utilize self-attention mechanisms to model long-range dependencies.",
                rerank_score=0.95
            ),
            RetrievalResult(
                rank=2,
                score=0.88,
                retrieval_type="reranked",
                document_id="doc_1",
                document_name="deep_learning_paper.pdf",
                page_number=4,
                chunk_id="chunk_dl_002",
                text="Multi-head attention allows the model to jointly attend to information from different representation subspaces.",
                rerank_score=0.89
            ),
            RetrievalResult(
                rank=3,
                score=0.75,
                retrieval_type="reranked",
                document_id="doc_2",
                document_name="system_architecture.pdf",
                page_number=12,
                chunk_id="chunk_sa_005",
                text="The prompt builder transforms cross-encoder results into structured prompts for downstream LLMs.",
                rerank_score=0.81
            )
        ]

    def tearDown(self):
        self.app_context.pop()

    def test_template_loading_and_fallback(self):
        """Verify template loading succeeds for valid template and falls back gracefully when missing."""
        content, actual_ver, is_fallback = self.service.load_template("rag_prompt_v1")
        self.assertIn("SYSTEM INSTRUCTIONS", content)
        self.assertEqual(actual_ver, "rag_prompt_v1")
        self.assertFalse(is_fallback)

        # Non-existent template version triggers fallback to rag_prompt_v1
        content_fb, actual_ver_fb, is_fallback_fb = self.service.load_template("non_existent_mode_999")
        self.assertIn("SYSTEM INSTRUCTIONS", content_fb)
        self.assertEqual(actual_ver_fb, "rag_prompt_v1")
        self.assertTrue(is_fallback_fb)

    def test_prompt_generation_metadata_and_hashing(self):
        """Verify prompt generation contains expected metadata, SHA-256 hash, version tags, and instructions."""
        query = "How does multi-head attention work?"
        result = self.service.build_prompt(query, self.sample_chunks)

        prompt = result["prompt"]
        self.assertIn(query, prompt)
        self.assertEqual(result["context_chunk_count"], 3)
        self.assertEqual(result["prompt_version"], "1.0.0")
        self.assertEqual(result["pipeline_version"], "1.0.0")
        self.assertIn("rag_prompt_v1", result["template_version"])

        # SHA-256 Hash verification
        expected_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        self.assertEqual(result["prompt_hash"], expected_hash)
        self.assertEqual(len(result["prompt_hash"]), 64)

    def test_evidence_deduplication_and_order_preservation(self):
        """Verify evidence deduplication removes duplicates while strictly keeping highest-ranked Cross-Encoder position."""
        duplicate_chunks = [
            self.sample_chunks[0],  # rank 1
            RetrievalResult(        # exact duplicate chunk_id
                rank=2, score=0.90, retrieval_type="reranked", document_id="doc_1",
                document_name="deep_learning_paper.pdf", page_number=3, chunk_id="chunk_dl_001",
                text="Transformers utilize self-attention mechanisms to model long-range dependencies.",
                rerank_score=0.90
            ),
            self.sample_chunks[1]   # rank 3
        ]

        deduped = self.service.deduplicate_and_preserve_order(duplicate_chunks)
        self.assertEqual(len(deduped), 2)
        self.assertEqual(deduped[0].chunk_id, "chunk_dl_001")
        self.assertEqual(deduped[1].chunk_id, "chunk_dl_002")

    def test_empty_query_handling(self):
        """Verify prompt builder handles empty query gracefully with warning in validation report."""
        result = self.service.build_prompt("", self.sample_chunks)
        self.assertTrue(result["prompt"])
        self.assertIn("[No user query provided]", result["prompt"])
        self.assertIn("User query is empty", result["validation"]["warnings"][0])

    def test_empty_retrieval_handling(self):
        """Verify prompt builder handles empty retrieval results list gracefully."""
        query = "What is quantum computing?"
        result = self.service.build_prompt(query, [])

        prompt = result["prompt"]
        self.assertIn(query, prompt)
        self.assertEqual(result["context_chunk_count"], 0)
        self.assertIn("No relevant evidence chunks retrieved", prompt)
        self.assertIn("Total Evidence Chunks: 0", prompt)

    def test_character_limits_and_truncation(self):
        """Verify character limits trigger prompt truncation when max_chars budget is tiny."""
        query = "Summarize deep learning mechanics."
        result = self.service.build_prompt(query, self.sample_chunks, max_chars=300)

        self.assertTrue(result["truncated"])
        self.assertLessEqual(result["character_count"], 300)
        self.assertIn("[NOTICE: Prompt context truncated", result["prompt"])

    def test_validation_layer_error_raising(self):
        """Verify PromptValidator raises PromptValidationError on invalid max_chars parameter."""
        with self.assertRaises(PromptValidationError):
            self.service.build_prompt("Query test", self.sample_chunks, max_chars=50)

    @patch('app.routes.prompt.logger')
    @patch('app.routes.prompt.HybridRetrievalService.search')
    @patch('app.routes.prompt.CrossEncoderService.rerank')
    def test_api_prompt_build_pipeline_endpoint(self, mock_rerank, mock_hybrid, mock_logger):
        """Verify REST API POST /api/prompt/build runs full pipeline and returns complete JSON response."""
        mock_hybrid.return_value = self.sample_chunks
        mock_rerank.return_value = self.sample_chunks

        response = self.client.post(
            "/api/prompt/build",
            json={"query": "How do attention mechanisms work?", "top_k": 3}
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["query"], "How do attention mechanisms work?")
        self.assertIn("prompt", data)
        self.assertIn("prompt_hash", data)
        self.assertIn("prompt_version", data)
        self.assertIn("pipeline_version", data)
        self.assertIn("validation", data)
        self.assertEqual(data["context_chunk_count"], 3)

    def test_api_prompt_build_provided_results(self):
        """Verify REST API POST /api/prompt/build accepts explicit results array."""
        dict_chunks = [c.to_dict() for c in self.sample_chunks[:2]]

        response = self.client.post(
            "/api/prompt/build",
            json={
                "query": "Test with provided results",
                "results": dict_chunks
            }
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["context_chunk_count"], 2)

    def test_api_missing_query_error(self):
        """Verify REST API returns 400 error when query parameter is missing."""
        response = self.client.post(
            "/api/prompt/build",
            json={"top_k": 5}
        )

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertIn("Missing 'query' parameter", data["message"])

if __name__ == "__main__":
    unittest.main()
