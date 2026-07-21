import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from app import create_app
from app.services.evaluation_service import EvaluationService
from app.services.evaluation_dataset import EvaluationDatasetService

class TestEvaluationMetrics(unittest.TestCase):
    """Unit tests for RAGAS and Retrieval quality metric calculations."""

    def setUp(self):
        self.eval_service = EvaluationService(
            hybrid_retriever=MagicMock(),
            prompt_builder=MagicMock(),
            llm_service=MagicMock(),
            dataset_service=MagicMock()
        )
        self.sample_chunks = [
            {
                "chunk_id": "c1",
                "document_name": "research_paper.pdf",
                "page_number": 1,
                "text": "Retrieval Augmented Generation combines vector search with neural language models."
            },
            {
                "chunk_id": "c2",
                "document_name": "ai_handbook.pdf",
                "page_number": 3,
                "text": "Cross-encoders compute fine-grained relevance scores between queries and passages."
            }
        ]

    def test_retrieval_precision_matching_doc(self):
        score = self.eval_service.compute_retrieval_precision(
            self.sample_chunks,
            expected_documents=["research_paper.pdf"]
        )
        self.assertEqual(score, 0.5)

    def test_retrieval_recall_matching_pages(self):
        score = self.eval_service.compute_retrieval_recall(
            self.sample_chunks,
            expected_pages=[1, 3]
        )
        self.assertEqual(score, 1.0)

    def test_context_precision(self):
        score = self.eval_service.compute_context_precision(
            self.sample_chunks,
            ground_truth="Retrieval Augmented Generation neural language models"
        )
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_context_recall(self):
        score = self.eval_service.compute_context_recall(
            self.sample_chunks,
            ground_truth="Retrieval Augmented Generation combines vector search. Cross-encoders compute relevance."
        )
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_faithfulness(self):
        answer = "Retrieval Augmented Generation combines vector search with neural language models."
        score = self.eval_service.compute_faithfulness(answer, self.sample_chunks)
        self.assertEqual(score, 1.0)

    def test_answer_relevancy(self):
        question = "What is Retrieval Augmented Generation?"
        answer = "Retrieval Augmented Generation combines neural models with vector search."
        score = self.eval_service.compute_answer_relevancy(question, answer)
        self.assertGreater(score, 0.5)

    def test_citation_coverage_and_accuracy(self):
        answer = "Retrieval Augmented Generation uses vector search [Doc: research_paper.pdf, Page 1]."
        cov = self.eval_service.compute_citation_coverage(answer)
        acc = self.eval_service.compute_citation_accuracy(answer, self.sample_chunks)
        self.assertEqual(cov, 1.0)
        self.assertEqual(acc, 1.0)


class TestEvaluationDataset(unittest.TestCase):
    """Unit tests for EvaluationDatasetService JSON persistence and reporting."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.dataset_service = EvaluationDatasetService(storage_dir=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_add_and_get_dataset(self):
        entry = self.dataset_service.add_dataset_entry(
            question="What is RAG?",
            ground_truth="RAG stands for Retrieval-Augmented Generation.",
            expected_documents=["rag_paper.pdf"],
            expected_pages=[1]
        )
        self.assertIn("id", entry)
        self.assertEqual(entry["question"], "What is RAG?")

        ds = self.dataset_service.get_dataset()
        self.assertEqual(len(ds), 1)
        self.assertEqual(ds[0]["question"], "What is RAG?")

    def test_history_and_report(self):
        run1 = {
            "question": "Q1",
            "overall_score": 0.85,
            "metrics": {
                "context_precision": 0.9,
                "context_recall": 0.8,
                "faithfulness": 1.0,
                "answer_relevancy": 0.8,
                "retrieval_precision": 0.8,
                "retrieval_recall": 0.8,
                "citation_coverage": 1.0,
                "citation_accuracy": 1.0
            }
        }
        self.dataset_service.save_evaluation_run(run1)

        history = self.dataset_service.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["question"], "Q1")

        report = self.dataset_service.get_report_statistics()
        self.assertEqual(report["total_evaluations"], 1)
        self.assertEqual(report["overall_score_avg"], 0.85)
        self.assertEqual(report["metrics_averages"]["faithfulness"], 1.0)


class TestEvaluationApiRoutes(unittest.TestCase):
    """Integration tests for Flask API endpoints."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["EVALUATION_DATASET_PATH"] = self.temp_dir
        self.client = self.app.test_client()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("app.routes.evaluation.EvaluationService")
    def test_run_evaluation_endpoint(self, mock_service_cls):
        mock_instance = MagicMock()
        mock_instance.evaluate_query.return_value = {
            "question": "Test Q",
            "overall_score": 0.9,
            "metrics": {"faithfulness": 1.0}
        }
        mock_service_cls.return_value = mock_instance

        resp = self.client.post("/api/evaluation/run", json={"question": "Test Q"})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["overall_score"], 0.9)

    def test_dataset_endpoints(self):
        # Create dataset entry
        post_resp = self.client.post("/api/evaluation/dataset", json={
            "question": "What is vector search?",
            "ground_truth": "Vector search finds nearest neighbors in embedding space."
        })
        self.assertEqual(post_resp.status_code, 201)

        # List dataset entries
        get_resp = self.client.get("/api/evaluation/dataset")
        self.assertEqual(get_resp.status_code, 200)
        data = get_resp.get_json()
        self.assertEqual(len(data["data"]), 1)

    def test_history_and_report_endpoints(self):
        hist_resp = self.client.get("/api/evaluation/history")
        self.assertEqual(hist_resp.status_code, 200)

        rep_resp = self.client.get("/api/evaluation/report")
        self.assertEqual(rep_resp.status_code, 200)
        self.assertTrue(rep_resp.get_json()["success"])

if __name__ == "__main__":
    unittest.main()
