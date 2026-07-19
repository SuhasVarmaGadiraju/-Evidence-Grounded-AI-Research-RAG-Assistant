import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import requests

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.services.llm_service import (
    LLMService,
    LLMServiceError,
    LLMAuthenticationError,
    LLMTimeoutError
)
from app.services.nvidia_client import NVIDIAClient
from app.services.base_retriever import RetrievalResult

class TestLLMService(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['NVIDIA_API_KEY'] = "mock_valid_nvidia_key_12345"
        self.app.config['NVIDIA_BASE_URL'] = "https://integrate.api.nvidia.com/v1"
        self.app.config['NVIDIA_MODEL'] = "meta/llama-3.1-70b-instruct"
        self.app.config['LLM_TIMEOUT'] = 5

        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

        self.nvidia_client = NVIDIAClient(
            api_key="mock_valid_nvidia_key_12345",
            base_url="https://integrate.api.nvidia.com/v1",
            model="meta/llama-3.1-70b-instruct"
        )
        self.service = LLMService(client=self.nvidia_client)

    def tearDown(self):
        self.app_context.pop()

    @patch('requests.Session.post')

    def test_successful_api_response_and_metadata_parsing(self, mock_post):
        """Verify successful response returns parsed answer, request_id, token breakdown, and finish_reason."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {"content": "Transformers use self-attention to process text [deep_learning_paper.pdf, Page 3]."},
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "total_tokens": 150,
                "prompt_tokens": 100,
                "completion_tokens": 50
            }
        }
        mock_post.return_value = mock_response

        res = self.service.generate("Test prompt string", request_id="custom_req_001")

        self.assertEqual(res["request_id"], "custom_req_001")
        self.assertIn("Transformers use self-attention", res["answer"])
        self.assertEqual(res["model"], "meta/llama-3.1-70b-instruct")
        self.assertEqual(res["finish_reason"], "stop")
        self.assertEqual(res["prompt_tokens"], 100)
        self.assertEqual(res["completion_tokens"], 50)
        self.assertEqual(res["total_tokens"], 150)
        self.assertEqual(res["retry_count"], 0)
        self.assertGreaterEqual(res["latency"], 0.0)

    def test_request_id_autogeneration(self):
        """Verify request_id is automatically generated as UUID hex string if omitted."""
        mock_client = MagicMock()
        mock_client.model = "meta/llama-3.1-70b-instruct"
        mock_client.post_chat_completion.return_value = (
            {
                "choices": [{"message": {"content": "Generated response"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
            },
            200,
            0
        )
        svc = LLMService(client=mock_client)
        res = svc.generate("Sample prompt")

        self.assertTrue(res["request_id"])
        self.assertEqual(len(res["request_id"]), 32)  # UUID4 hex length

    def test_health_check_local_verification(self):
        """Verify health check returns local status without making network requests."""
        health = self.service.health_check()
        self.assertEqual(health["provider"], "NVIDIA")
        self.assertTrue(health["configured"])
        self.assertEqual(health["model"], "meta/llama-3.1-70b-instruct")
        self.assertEqual(health["service_status"], "healthy")

        # GET /api/chat/health route
        response = self.client.get("/api/chat/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["provider"], "NVIDIA")

    def test_empty_prompt_validation(self):
        """Verify error raised when empty or whitespace prompt is passed."""
        with self.assertRaises(LLMServiceError):
            self.service.generate("")

        with self.assertRaises(LLMServiceError):
            self.service.generate(None)

    def test_missing_or_invalid_api_key(self):
        """Verify LLMAuthenticationError raised when API key is missing or default placeholder."""
        unauth_client = NVIDIAClient(api_key="", base_url="https://integrate.api.nvidia.com/v1")
        unauth_service = LLMService(client=unauth_client)
        with self.assertRaises(LLMAuthenticationError):
            unauth_service.generate("Test prompt")

        placeholder_client = NVIDIAClient(api_key="your_nvidia_api_key_here")
        placeholder_service = LLMService(client=placeholder_client)
        with self.assertRaises(LLMAuthenticationError):
            placeholder_service.generate("Test prompt")

    @patch('requests.Session.post')

    def test_no_retries_on_authentication_failure(self, mock_post):
        """Verify 401 Unauthorized raises LLMAuthenticationError immediately without retrying."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        with self.assertRaises(LLMAuthenticationError):
            self.service.generate("Test prompt")

        # Crucial security rule: exactly 1 call (NO retries)
        self.assertEqual(mock_post.call_count, 1)

    @patch('requests.Session.post')

    def test_timeout_handling(self, mock_post):
        """Verify request timeout exception maps to LLMTimeoutError after retries."""
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        with self.assertRaises(LLMTimeoutError):
            self.service.generate("Test prompt")

        # Confirm 3 retry attempts were made
        self.assertEqual(mock_post.call_count, 3)

    @patch('time.sleep')
    @patch('requests.Session.post')

    def test_exponential_backoff_retry_logic(self, mock_post, mock_sleep):
        """Verify backoff retry logic retries twice on failure and succeeds on 3rd attempt."""
        fail_res = MagicMock()
        fail_res.status_code = 503

        success_res = MagicMock()
        success_res.status_code = 200
        success_res.json.return_value = {
            "choices": [{"message": {"content": "Grounded answer after retry."}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 40, "completion_tokens": 10, "total_tokens": 50}
        }

        mock_post.side_effect = [fail_res, fail_res, success_res]

        res = self.service.generate("Test prompt")

        self.assertEqual(res["answer"], "Grounded answer after retry.")
        self.assertEqual(res["retry_count"], 2)
        self.assertEqual(mock_post.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch('requests.Session.post')

    def test_malformed_json_response_handling(self, mock_post):
        """Verify malformed JSON response raises LLMServiceError gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON format")
        mock_post.return_value = mock_response

        with self.assertRaises(LLMServiceError):
            self.service.generate("Test prompt")

    @patch('app.routes.chat.HybridRetrievalService.search')
    @patch('app.routes.chat.CrossEncoderService.rerank')
    @patch('app.routes.chat.LLMService.generate')
    def test_api_chat_pipeline_endpoint(self, mock_llm_gen, mock_rerank, mock_hybrid):
        """Verify REST API POST /api/chat runs full RAG pipeline and returns structured answer JSON with request_id."""
        mock_chunks = [
            RetrievalResult(1, 0.9, "reranked", "d1", "research_paper.pdf", 5, "c1", "Attention is all you need.")
        ]
        mock_hybrid.return_value = mock_chunks
        mock_rerank.return_value = mock_chunks

        mock_llm_gen.return_value = {
            "request_id": "test_req_xyz_123",
            "answer": "Attention mechanisms allow long range context modeling [research_paper.pdf, Page 5].",
            "model": "meta/llama-3.1-70b-instruct",
            "latency": 0.85,
            "retry_count": 0,
            "finish_reason": "stop",
            "prompt_tokens": 100,
            "completion_tokens": 20,
            "total_tokens": 120,
            "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120},
            "status_code": 200
        }

        response = self.client.post(
            "/api/chat",
            json={"query": "What are attention mechanisms?"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["request_id"], "test_req_xyz_123")
        self.assertEqual(data["query"], "What are attention mechanisms?")
        self.assertIn("Attention mechanisms allow", data["answer"])
        self.assertEqual(data["model"], "meta/llama-3.1-70b-instruct")
        self.assertIn("prompt_hash", data)
        self.assertEqual(data["finish_reason"], "stop")
        self.assertEqual(data["prompt_tokens"], 100)
        self.assertEqual(data["completion_tokens"], 20)
        self.assertEqual(data["estimated_tokens"], 120)
        self.assertEqual(len(data["citations"]), 1)
        self.assertEqual(data["citations"][0]["document_name"], "research_paper.pdf")

    def test_api_chat_missing_query(self):
        """Verify POST /api/chat returns 400 when query is missing."""
        response = self.client.post("/api/chat", json={})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])

if __name__ == "__main__":
    unittest.main()
