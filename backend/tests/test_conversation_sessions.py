import sys
import os
import io
import uuid
import unittest
from unittest.mock import patch, MagicMock

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from database.database import db
from database.models.user import User
from database.models.research_session import ResearchSession
from database.models.message import Message
from database.models.retrieval_log import RetrievalLog
from app.services.session_service import (
    create_session,
    get_session,
    rename_session,
    delete_session,
    append_message_turn,
    format_multi_turn_history,
    generate_session_title
)
from app.services.retrieval_log_service import (
    save_retrieved_chunks,
    get_retrieval_logs_for_message
)
from app.services.export_service import export_session_content

class TestConversationSessions(unittest.TestCase):
    def setUp(self):
        os.environ["FLASK_ENV"] = "testing"
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.rollback()
            db.session.remove()

    def test_auto_title_generation(self):
        """Verify automatic 3-8 word title generation from first question."""
        title1 = generate_session_title("What is the coffee market trends in South America?")
        self.assertIn("Coffee Market Trends", title1)

        title2 = generate_session_title("Can you explain battery fault diagnosis methods?")
        self.assertIn("Battery Fault", title2)

        title3 = generate_session_title("Tell me about hybrid search evaluation")
        self.assertIn("Hybrid Search Evaluation", title3)

    def test_session_lifecycle(self):
        """Test session creation, retrieval, rename, and deletion in PostgreSQL."""
        with self.app.app_context():
            # 1. Create Session
            session = create_session(title="Initial Title")
            self.assertIsNotNone(session.id)
            self.assertEqual(session.title, "Initial Title")

            # 2. Get Session
            fetched = get_session(session.session_uuid)
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.id, session.id)

            # 3. Rename Session
            renamed = rename_session(session.session_uuid, "Updated Research Title")
            self.assertEqual(renamed.title, "Updated Research Title")

            # 4. Delete Session
            deleted = delete_session(session.session_uuid)
            self.assertTrue(deleted)
            self.assertIsNone(get_session(session.session_uuid))

    def test_message_persistence_and_auto_title_trigger(self):
        """Verify appending messages triggers auto-title generation on default session."""
        with self.app.app_context():
            session = create_session() # default title "New Research Session"
            self.assertEqual(session.title, "New Research Session")

            # Append turn 1
            msg1, s1 = append_message_turn(
                session.session_uuid,
                user_question="What is the medical report analysis for diabetes?",
                assistant_answer="Medical analysis shows insulin resistance parameters.",
                latency=1.25,
                token_count=150
            )

            self.assertIsNotNone(msg1.id)
            self.assertIn("Medical Report Analysis", s1.title)

            # Verify history length
            history = format_multi_turn_history(session.session_uuid)
            self.assertEqual(len(history), 2)
            self.assertEqual(history[0]["role"], "user")
            self.assertEqual(history[1]["role"], "assistant")

    def test_retrieval_logging_and_scores(self):
        """Verify saving and retrieving fine-grained evidence attribution and 4-score breakdown."""
        with self.app.app_context():
            session = create_session(title="Retrieval Log Test")
            msg, s = append_message_turn(
                session.session_uuid,
                user_question="Hybrid retrieval performance",
                assistant_answer="RRF fuses BM25 and vector ranks."
            )

            chunks_data = [
                {
                    "document_id": "doc_uuid_1001",
                    "chunk_id": "chunk_uuid_2001",
                    "page_number": 5,
                    "faiss_vector_id": 42,
                    "scores": {"semantic": 0.89, "bm25": 14.2, "rrf": 0.033, "cross_encoder": 4.15}
                },
                {
                    "document_id": "doc_uuid_1001",
                    "chunk_id": "chunk_uuid_2002",
                    "page_number": 6,
                    "faiss_vector_id": 43,
                    "scores": {"semantic": 0.75, "bm25": 9.1, "rrf": 0.021, "cross_encoder": 2.85}
                }
            ]

            logs = save_retrieved_chunks(msg.id, chunks_data, strategy="Hybrid RRF")
            self.assertEqual(len(logs), 2)

            retrieved = get_retrieval_logs_for_message(msg.id)
            self.assertEqual(len(retrieved), 2)
            self.assertEqual(retrieved[0]["retrieval_strategy"], "Hybrid RRF")
            self.assertEqual(retrieved[0]["retrieval_rank"], 1)
            self.assertEqual(retrieved[1]["retrieval_rank"], 2)
            self.assertEqual(retrieved[0]["bm25_score"], 14.2)
            self.assertEqual(retrieved[0]["reranker_score"], 4.15)

    def test_cascading_deletion(self):
        """Verify deleting a session cascade-deletes messages and retrieval logs in PostgreSQL."""
        with self.app.app_context():
            session = create_session(title="Cascade Delete Test")
            msg, s = append_message_turn(
                session.session_uuid,
                user_question="Cascade question",
                assistant_answer="Cascade answer"
            )

            chunks_data = [{
                "document_id": "doc_cascade_1",
                "chunk_id": "chunk_cascade_1",
                "page_number": 1,
                "scores": {"semantic": 0.8, "bm25": 10.0, "rrf": 0.03, "cross_encoder": 3.0}
            }]
            save_retrieved_chunks(msg.id, chunks_data)

            msg_id = msg.id
            self.assertIsNotNone(Message.query.get(msg_id))
            self.assertEqual(RetrievalLog.query.filter_by(message_id=msg_id).count(), 1)

            # Delete Session
            delete_session(session.session_uuid)

            # Confirm Messages and RetrievalLogs deleted
            self.assertIsNone(Message.query.get(msg_id))
            self.assertEqual(RetrievalLog.query.filter_by(message_id=msg_id).count(), 0)

    def test_session_export(self):
        """Verify session export for Markdown, JSON, and PDF formats."""
        with self.app.app_context():
            session = create_session(title="Export Test Session")
            msg, s = append_message_turn(
                session.session_uuid,
                user_question="Explain RAG evaluation",
                assistant_answer="RAG evaluation measures context precision and answer relevance."
            )

            # Markdown
            md_bytes, md_mime, md_file = export_session_content(session.session_uuid, "markdown")
            self.assertEqual(md_mime, "text/markdown")
            self.assertIn("Export Test Session", md_bytes)

            # JSON
            json_bytes, json_mime, json_file = export_session_content(session.session_uuid, "json")
            self.assertEqual(json_mime, "application/json")
            self.assertIn("Export Test Session", json_bytes)

            # PDF
            pdf_bytes, pdf_mime, pdf_file = export_session_content(session.session_uuid, "pdf")
            self.assertEqual(pdf_mime, "application/pdf")
            self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_session_rest_api(self):
        """Verify REST API routes for sessions."""
        # 1. POST /api/sessions
        res_create = self.client.post("/api/sessions", json={"title": "REST API Session"})
        self.assertEqual(res_create.status_code, 201)
        session_id = res_create.get_json()["session"]["session_id"]

        # 2. GET /api/sessions
        res_list = self.client.get("/api/sessions")
        self.assertEqual(res_list.status_code, 200)

        # 3. GET /api/sessions/<session_id>
        res_get = self.client.get(f"/api/sessions/{session_id}")
        self.assertEqual(res_get.status_code, 200)

        # 4. PATCH /api/sessions/<session_id>
        res_patch = self.client.patch(f"/api/sessions/{session_id}", json={"title": "Renamed API Title"})
        self.assertEqual(res_patch.status_code, 200)
        self.assertEqual(res_patch.get_json()["session"]["title"], "Renamed API Title")

        # 5. DELETE /api/sessions/<session_id>
        res_del = self.client.delete(f"/api/sessions/{session_id}")
        self.assertEqual(res_del.status_code, 200)

        # 6. Verify 404
        res_404 = self.client.get(f"/api/sessions/{session_id}")
        self.assertEqual(res_404.status_code, 404)

    def test_multi_turn_chat_integration(self):
        """Verify /api/chat endpoint multi-turn context, latency breakdown, and attribution logging."""
        with patch("app.routes.chat.HybridRetrievalService") as mock_hybrid_cls, \
             patch("app.routes.chat.CrossEncoderService") as mock_cross_cls, \
             patch("app.routes.chat.LLMService") as mock_llm_cls:

            mock_hybrid = MagicMock(spec=["search"])
            mock_hybrid.search.return_value = [
                {"document_id": "doc_test_99", "chunk_id": "chunk_test_99", "page_number": 2, "text": "Sample text", "scores": {"semantic": 0.82, "bm25": 11.5, "rrf": 0.028}}
            ]
            mock_hybrid_cls.return_value = mock_hybrid

            mock_cross = MagicMock(spec=["_get_default_top_k", "rerank"])
            mock_cross._get_default_top_k.return_value = 3
            mock_cross.rerank.return_value = [
                {"document_id": "doc_test_99", "chunk_id": "chunk_test_99", "page_number": 2, "text": "Sample text", "scores": {"semantic": 0.82, "bm25": 11.5, "rrf": 0.028, "cross_encoder": 3.8}}
            ]
            mock_cross_cls.return_value = mock_cross

            mock_llm = MagicMock(spec=["generate"])
            mock_llm.generate.return_value = {
                "answer": "Grounded answer text for multi-turn test.",
                "model": "meta/llama-3.1-405b-instruct",
                "request_id": "req_integration_123",
                "prompt_tokens": 120,
                "completion_tokens": 30,
                "total_tokens": 150,
                "finish_reason": "stop"
            }
            mock_llm_cls.return_value = mock_llm

            # First turn
            res1 = self.client.post("/api/chat", json={"question": "What is hybrid search?"})
            self.assertEqual(res1.status_code, 200)
            data1 = res1.get_json()
            session_id = data1["session_id"]
            self.assertEqual(data1["conversation_length"], 1)
            self.assertEqual(data1["embedding_model"], "all-MiniLM-L6-v2")
            self.assertEqual(data1["cross_encoder_model"], "cross-encoder/ms-marco-MiniLM-L-6-v2")

            # Second turn (same session)
            res2 = self.client.post("/api/chat", json={"question": "How does RRF work?", "session_id": session_id})
            self.assertEqual(res2.status_code, 200)
            data2 = res2.get_json()
            self.assertEqual(data2["session_id"], session_id)
            self.assertEqual(data2["conversation_length"], 2)

if __name__ == "__main__":
    unittest.main()
