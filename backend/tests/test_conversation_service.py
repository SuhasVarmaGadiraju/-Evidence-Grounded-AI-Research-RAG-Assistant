import sys
import os
import time
import unittest


# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.services.conversation_service import ConversationService

class TestConversationService(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['MAX_CONVERSATION_TURNS'] = 3
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.service = ConversationService(default_max_turns=3)

    def tearDown(self):
        self.app_context.pop()

    def test_create_session_and_uuid_generation(self):
        """Verify session creation generates unique 32-character hex UUID session_id."""
        s1 = self.service.create_session(title="Research Session 1")
        s2 = self.service.create_session(title="Research Session 2")

        self.assertTrue(s1)
        self.assertTrue(s2)
        self.assertEqual(len(s1), 32)
        self.assertEqual(len(s2), 32)
        self.assertNotEqual(s1, s2)

    def test_add_and_retrieve_messages(self):
        """Verify adding user and assistant messages stores and retrieves structured history."""
        session_id = self.service.create_session()
        self.service.add_message(session_id, "user", "What is RAG?", request_id="req1")
        self.service.add_message(session_id, "assistant", "RAG is Retrieval-Augmented Generation.", citations=[{"doc": "p1.pdf"}], request_id="req1")

        history = self.service.get_history(session_id)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[0]["content"], "What is RAG?")
        self.assertEqual(history[1]["role"], "assistant")
        self.assertEqual(history[1]["content"], "RAG is Retrieval-Augmented Generation.")
        self.assertEqual(len(history[1]["citations"]), 1)

    def test_max_conversation_turns_pruning(self):
        """Verify session prunes old messages when exceeding max_turns limit."""
        session_id = self.service.create_session()
        
        # Max turns set to 3 = 6 messages max
        for i in range(1, 6):
            self.service.add_message(session_id, "user", f"Query {i}")
            self.service.add_message(session_id, "assistant", f"Answer {i}")

        history = self.service.get_history(session_id)
        self.assertEqual(len(history), 6)  # 3 turns = 6 messages max
        self.assertEqual(history[0]["content"], "Query 3")
        self.assertEqual(history[-1]["content"], "Answer 5")

    def test_session_deletion(self):
        """Verify session deletion removes session data and history."""
        session_id = self.service.create_session()
        self.service.add_message(session_id, "user", "Test message")

        deleted = self.service.delete_session(session_id)
        self.assertTrue(deleted)
        self.assertIsNone(self.service.get_session(session_id))
        self.assertEqual(self.service.get_history(session_id), [])

    def test_multi_session_isolation(self):
        """Verify messages in session A do not leak into session B."""
        s1 = self.service.create_session(title="Session A")
        s2 = self.service.create_session(title="Session B")

        self.service.add_message(s1, "user", "Session A Query")
        self.service.add_message(s2, "user", "Session B Query")

        h1 = self.service.get_history(s1)
        h2 = self.service.get_history(s2)

        self.assertEqual(len(h1), 1)
        self.assertEqual(len(h2), 1)
        self.assertEqual(h1[0]["content"], "Session A Query")
        self.assertEqual(h2[0]["content"], "Session B Query")

    def test_list_sessions_and_stats(self):
        """Verify listing sessions sorts by updated_at and returns correct stats."""
        s1 = self.service.create_session(title="First")
        time.sleep(0.01)
        s2 = self.service.create_session(title="Second")

        self.service.add_message(s1, "user", "Update first")

        sessions = self.service.list_sessions()
        self.assertEqual(len(sessions), 2)
        # s1 updated most recently
        self.assertEqual(sessions[0]["session_id"], s1)

        stats = self.service.get_stats()
        self.assertEqual(stats["active_sessions"], 2)
        self.assertEqual(stats["stored_messages"], 1)

if __name__ == "__main__":
    unittest.main()
