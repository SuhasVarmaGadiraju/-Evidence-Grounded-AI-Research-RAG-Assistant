import sys
import os
import time
import unittest
from unittest.mock import patch, MagicMock

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.utils.profiler import PipelineProfiler
from app.services.cache_service import LLMCache, RetrievalCache, get_all_cache_stats
from app.services.nvidia_client import NVIDIAClient, get_http_session
from app.services.prompt_builder import PromptBuilderService
from app.services.warmup import warmup_services

class TestPerformanceAndHardening(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['CACHE_ENABLED'] = True
        self.app.config['NVIDIA_API_KEY'] = "mock_valid_nvidia_key_12345"
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

    def tearDown(self):
        self.app_context.pop()

    def test_pipeline_profiler_stage_measurements(self):
        """Verify PipelineProfiler captures nanosecond stage timings correctly."""
        profiler = PipelineProfiler()
        with profiler.profile("hybrid_retrieval"):
            time.sleep(0.01)

        with profiler.profile("cross_encoder"):
            time.sleep(0.01)

        breakdown = profiler.get_breakdown()
        self.assertIn("hybrid_retrieval", breakdown)
        self.assertIn("cross_encoder", breakdown)
        self.assertIn("total", breakdown)
        self.assertGreaterEqual(breakdown["hybrid_retrieval"], 0.01)
        self.assertGreaterEqual(breakdown["total"], 0.02)

    def test_llm_cache_hit_miss_and_eviction(self):
        """Verify LLMCache stores responses, handles TTL, and evicts oldest items upon reaching capacity."""
        cache = LLMCache(max_size=2, ttl_seconds=2)
        
        # Test MISS
        self.assertIsNone(cache.get("Prompt 1"))

        # Test SET and HIT
        cache.set("Prompt 1", {"answer": "Answer 1"})
        hit_val = cache.get("Prompt 1")
        self.assertIsNotNone(hit_val)
        self.assertEqual(hit_val["answer"], "Answer 1")

        # Test Eviction upon max capacity
        cache.set("Prompt 2", {"answer": "Answer 2"})
        cache.set("Prompt 3", {"answer": "Answer 3"})
        self.assertIsNone(cache.get("Prompt 1"))  # Evicted
        self.assertIsNotNone(cache.get("Prompt 2"))
        self.assertIsNotNone(cache.get("Prompt 3"))

        # Check Cache Stats
        stats = cache.stats()
        self.assertEqual(stats["name"], "LLMCache")
        self.assertEqual(stats["size"], 2)
        self.assertGreaterEqual(stats["hits"], 3)
        self.assertGreaterEqual(stats["evictions"], 1)

    def test_retrieval_cache_hit_and_miss(self):
        """Verify RetrievalCache caches and returns retrieval outputs."""
        cache = RetrievalCache(max_size=5, ttl_seconds=10)
        self.assertIsNone(cache.get("query_1:5:v1"))

        cache.set("query_1:5:v1", {"prompt_result": {"prompt": "P1"}, "included_chunks": []})
        cached = cache.get("query_1:5:v1")
        self.assertIsNotNone(cached)
        self.assertEqual(cached["prompt_result"]["prompt"], "P1")

    def test_nvidia_client_session_reuse(self):
        """Verify NVIDIAClient reuses persistent requests.Session instance across calls."""
        session1 = get_http_session()
        session2 = get_http_session()
        self.assertIs(session1, session2)

        client = NVIDIAClient(api_key="mock_key")
        self.assertIs(client.session, session1)

    def test_prompt_minification_and_reduction(self):
        """Verify PromptBuilderService minifies prompt whitespace without altering text."""
        builder = PromptBuilderService()
        raw = "Line 1\n\n\n\nLine 2   \n\n\nLine 3\n"
        minified = builder.minify_prompt(raw)

        self.assertNotIn("\n\n\n", minified)
        self.assertIn("Line 1\n\nLine 2\n\nLine 3", minified)
        self.assertLess(len(minified), len(raw))

    def test_extended_health_endpoint_schema(self):
        """Verify GET /api/chat/health returns readiness checks, cache stats, and uptime."""
        response = self.client.get("/api/chat/health")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["provider"], "NVIDIA")
        self.assertIn("readiness", data)
        self.assertIn("cache_stats", data)
        self.assertIn("uptime_seconds", data)

        readiness = data["readiness"]
        self.assertIn("embedding_loaded", readiness)
        self.assertIn("cross_encoder_loaded", readiness)
        self.assertIn("bm25_ready", readiness)
        self.assertIn("faiss_ready", readiness)
        self.assertIn("prompt_template_loaded", readiness)

    def test_startup_warmup_services(self):
        """Verify warmup_services initializes pipeline models without error."""
        status = warmup_services(self.app)
        self.assertIn("embedding_loaded", status)
        self.assertIn("cross_encoder_loaded", status)
        self.assertIn("prompt_template_loaded", status)
        self.assertIn("warmup_time_seconds", status)

if __name__ == "__main__":
    unittest.main()
