import time
import uuid
import threading
import logging
from typing import Dict, Any, List, Optional
from flask import current_app

logger = logging.getLogger("rag_backend.services.conversation_service")

class ConversationService:
    """
    Thread-safe in-memory Conversation Service managing multi-turn chat sessions and message history.
    """

    def __init__(self, default_max_turns: int = 10):
        self.default_max_turns = default_max_turns
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def _get_max_turns(self) -> int:

        if current_app:
            return int(current_app.config.get("MAX_CONVERSATION_TURNS", self.default_max_turns))
        import os
        return int(os.getenv("MAX_CONVERSATION_TURNS", self.default_max_turns))

    def create_session(self, title: Optional[str] = None) -> str:
        """Creates a new conversation session and returns unique session_id."""
        session_id = uuid.uuid4().hex
        now = time.time()

        session_data = {
            "session_id": session_id,
            "title": title or "New Conversation",
            "created_at": now,
            "updated_at": now,
            "messages": []
        }

        with self._lock:
            self._sessions[session_id] = session_data

        logger.info(f"Created conversation session: {session_id[:12]}...")
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves session dictionary if exists."""
        with self._lock:
            return self._sessions.get(session_id)

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        citations: Optional[List[Dict[str, Any]]] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Appends user or assistant message to session history, pruning old messages beyond max_turns limit.
        """
        now = time.time()
        msg_obj = {
            "role": role,
            "content": content,
            "timestamp": now,
            "citations": citations or [],
            "request_id": request_id
        }

        with self._lock:
            if session_id not in self._sessions:
                # Auto-create session if missing
                self._sessions[session_id] = {
                    "session_id": session_id,
                    "title": content[:40] if role == "user" else "New Conversation",
                    "created_at": now,
                    "updated_at": now,
                    "messages": []
                }

            session = self._sessions[session_id]
            session["updated_at"] = now

            # Auto-set session title from first user query
            if role == "user" and (session["title"] == "New Conversation" or not session["messages"]):
                session["title"] = content[:40].strip() + ("..." if len(content) > 40 else "")

            session["messages"].append(msg_obj)

            # Limit history to MAX_CONVERSATION_TURNS (each turn = 1 user + 1 assistant message)
            max_turns = self._get_max_turns()
            max_messages = max_turns * 2
            if len(session["messages"]) > max_messages:
                # Keep most recent max_messages
                session["messages"] = session["messages"][-max_messages:]
                logger.debug(f"Pruned session {session_id[:8]} messages to max {max_messages} entries.")

        return msg_obj

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Returns list of stored messages for a session."""
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return []
            return list(session.get("messages", []))

    def delete_session(self, session_id: str) -> bool:
        """Deletes session and returns True if found."""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.info(f"Deleted conversation session: {session_id[:12]}...")
                return True
            return False

    def list_sessions(self) -> List[Dict[str, Any]]:
        """Returns summary list of all active sessions sorted by latest activity descending."""
        with self._lock:
            sessions_list = []
            for s_id, s_data in self._sessions.items():
                msg_count = len(s_data.get("messages", []))
                turns_count = msg_count // 2
                sessions_list.append({
                    "session_id": s_id,
                    "title": s_data.get("title", "New Conversation"),
                    "created_at": s_data.get("created_at", 0),
                    "updated_at": s_data.get("updated_at", 0),
                    "message_count": msg_count,
                    "turns_count": turns_count
                })

            # Sort by updated_at descending
            sessions_list.sort(key=lambda x: x["updated_at"], reverse=True)
            return sessions_list

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics for observability and health endpoints."""
        with self._lock:
            total_sessions = len(self._sessions)
            total_messages = sum(len(s.get("messages", [])) for s in self._sessions.values())
            return {
                "active_sessions": total_sessions,
                "stored_messages": total_messages
            }

# Global ConversationService singleton
conversation_service = ConversationService()
