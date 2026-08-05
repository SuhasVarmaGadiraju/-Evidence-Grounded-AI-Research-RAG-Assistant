import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from database.database import db
from database.models.research_session import ResearchSession
from database.models.message import Message
from database.models.user import User

logger = logging.getLogger("rag_backend.services.session_service")

DEFAULT_SESSION_TITLE = "New Research Session"

def generate_session_title(first_question: str) -> str:
    """
    Generates a concise 3-8 word title based on the first user question or context.
    Strips common query prefixes (e.g. 'what is', 'explain', 'tell me about')
    and formats the key subject as a clean Title Case string.

    Examples:
        - "What is the coffee market trends?" -> "Coffee Market Trends Analysis"
        - "Battery fault diagnosis overview" -> "Battery Fault Diagnosis Overview"
        - "Can you explain hybrid search evaluation?" -> "Hybrid Search Evaluation"

    Args:
        first_question (str): The initial user question text.

    Returns:
        str: Concise session title (3 to 8 words).
    """
    if not first_question or not first_question.strip():
        return "Research Discussion"

    text = first_question.strip()
    lower_text = text.lower()

    # Remove common conversational query prefixes
    prefixes = [
        "what is the", "what is", "what are the", "what are",
        "can you explain", "explain the", "explain",
        "tell me about the", "tell me about", "tell me",
        "how to", "how do i", "how does",
        "describe the", "describe", "give me details on",
        "summarize the", "summarize", "analyze the", "analyze"
    ]

    for prefix in prefixes:
        if lower_text.startswith(prefix):
            text = text[len(prefix):].strip(" ?:!.,-")
            break

    words = [w.strip(" ?:!.,-") for w in text.split() if w.strip(" ?:!.,-")]
    if not words:
        return "Research Discussion"

    # Limit to 3-8 words
    title_words = words[:min(len(words), 7)]
    title = " ".join(title_words).title()

    if len(title.split()) < 2:
        title += " Analysis"

    return title[:255]

def create_session(user_info: Optional[Dict[str, Any]] = None, title: Optional[str] = None) -> ResearchSession:
    """
    Creates a new ResearchSession in PostgreSQL within a database transaction.

    Args:
        user_info (Optional[Dict[str, Any]]): Authenticated user payload containing firebase_uid or email.
        title (Optional[str]): Optional custom title for the session.

    Returns:
        ResearchSession: Newly created session ORM instance.

    Raises:
        RuntimeError: If database transaction fails.
    """
    session_id = str(uuid.uuid4())
    session_title = title.strip() if title and title.strip() else DEFAULT_SESSION_TITLE
    user_db_id = None

    if user_info:
        firebase_uid = user_info.get("firebase_uid") or user_info.get("uid") or user_info.get("id")
        email = user_info.get("email")
        if firebase_uid or email:
            try:
                user = User.query.filter(
                    (User.firebase_uid == firebase_uid) | (User.email == email)
                ).first()
                if user:
                    user_db_id = user.id
            except Exception as e:
                logger.warning(f"Failed to resolve user for session creation: {e}")

    now = datetime.now(timezone.utc)
    session = ResearchSession(
        session_uuid=session_id,
        title=session_title,
        user_id=user_db_id,
        created_at=now,
        updated_at=now
    )

    try:
        db.session.add(session)
        db.session.commit()
        logger.info(f"Created ResearchSession ID={session.id} UUID='{session_id}' title='{session_title}'")
        return session
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Failed to create ResearchSession: {e}")
        raise RuntimeError(f"Session creation failed: {str(e)}") from e

def get_session(session_id_or_uuid: str) -> Optional[ResearchSession]:
    """
    Retrieves a ResearchSession by session_uuid or integer primary key.

    Args:
        session_id_or_uuid (str): Session UUID string or integer ID string.

    Returns:
        Optional[ResearchSession]: Found ResearchSession or None.
    """
    if not session_id_or_uuid:
        return None

    try:
        # Try lookup by session_uuid
        session = ResearchSession.query.filter_by(session_uuid=session_id_or_uuid).first()
        if session:
            return session

        # Fallback to integer primary key lookup
        if str(session_id_or_uuid).isdigit():
            return ResearchSession.query.get(int(session_id_or_uuid))
    except Exception as e:
        logger.error(f"Error retrieving session '{session_id_or_uuid}': {e}")

    return None

def list_sessions(user_info: Optional[Dict[str, Any]] = None) -> List[ResearchSession]:
    """
    Lists all ResearchSessions sorted by last activity (updated_at DESC).
    Scopes to user if user_info is provided.

    Args:
        user_info (Optional[Dict[str, Any]]): Optional user info payload.

    Returns:
        List[ResearchSession]: List of session ORM objects.
    """
    try:
        query = ResearchSession.query
        user_db_id = None

        if user_info:
            firebase_uid = user_info.get("firebase_uid") or user_info.get("uid") or user_info.get("id")
            email = user_info.get("email")
            if firebase_uid or email:
                user = User.query.filter(
                    (User.firebase_uid == firebase_uid) | (User.email == email)
                ).first()
                if user:
                    user_db_id = user.id

        if user_db_id:
            query = query.filter(ResearchSession.user_id == user_db_id)

        return query.order_by(ResearchSession.updated_at.desc()).all()
    except Exception as e:
        logger.error(f"Failed to list sessions from PostgreSQL: {e}")
        return []

def rename_session(session_id_or_uuid: str, new_title: str) -> ResearchSession:
    """
    Renames a ResearchSession in PostgreSQL within a database transaction.

    Args:
        session_id_or_uuid (str): Session UUID or ID.
        new_title (str): New title string.

    Returns:
        ResearchSession: Updated ResearchSession object.

    Raises:
        ValueError: If title is empty or session not found.
        RuntimeError: If database update transaction fails.
    """
    clean_title = new_title.strip() if new_title else ""
    if not clean_title:
        raise ValueError("New session title cannot be empty.")

    session = get_session(session_id_or_uuid)
    if not session:
        raise ValueError(f"ResearchSession '{session_id_or_uuid}' not found.")

    try:
        session.title = clean_title
        session.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        logger.info(f"Renamed ResearchSession ID={session.id} -> '{clean_title}'")
        return session
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Failed to rename session '{session_id_or_uuid}': {e}")
        raise RuntimeError(f"Session rename transaction failed: {str(e)}") from e

def delete_session(session_id_or_uuid: str) -> bool:
    """
    Deletes a ResearchSession from PostgreSQL within a database transaction.
    Cascade-deletes all associated Message and RetrievalLog records automatically.

    Args:
        session_id_or_uuid (str): Session UUID or ID.

    Returns:
        bool: True if deleted successfully, False if session not found.

    Raises:
        RuntimeError: If database deletion transaction fails.
    """
    session = get_session(session_id_or_uuid)
    if not session:
        return False

    try:
        db.session.delete(session)
        db.session.commit()
        logger.info(f"Deleted ResearchSession ID={session.id} UUID='{session.session_uuid}' (cascaded messages & logs)")
        return True
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Failed to delete session '{session_id_or_uuid}': {e}")
        raise RuntimeError(f"Session deletion transaction failed: {str(e)}") from e

def load_session_history(session_id_or_uuid: str) -> Dict[str, Any]:
    """
    Loads full conversation history and chunk attribution logs for a session.

    Args:
        session_id_or_uuid (str): Session UUID or ID.

    Returns:
        Dict[str, Any]: Formatted session history payload.

    Raises:
        ValueError: If session is not found.
    """
    session = get_session(session_id_or_uuid)
    if not session:
        raise ValueError(f"ResearchSession '{session_id_or_uuid}' not found.")

    return session.to_dict(include_messages=True)

def append_message_turn(
    session_id_or_uuid: str,
    user_question: str,
    assistant_answer: str,
    latency: float = 0.0,
    token_count: int = 0,
    role: str = "assistant"
) -> Tuple[Message, ResearchSession]:
    """
    Appends a Q&A message turn to a session in a database transaction.
    Automatically generates a 3-8 word title if session title is still default.

    Args:
        session_id_or_uuid (str): Session UUID or ID.
        user_question (str): User prompt text.
        assistant_answer (str): Assistant answer text.
        latency (float): Processing latency in seconds.
        token_count (int): Token count for turn.
        role (str): Role string ('assistant').

    Returns:
        Tuple[Message, ResearchSession]: Created Message object and updated ResearchSession.

    Raises:
        ValueError: If session not found.
        RuntimeError: If database transaction fails.
    """
    session = get_session(session_id_or_uuid)
    if not session:
        raise ValueError(f"ResearchSession '{session_id_or_uuid}' not found.")

    now = datetime.now(timezone.utc)
    msg_id = str(uuid.uuid4())

    try:
        message = Message(
            message_uuid=msg_id,
            session_id=session.id,
            role=role,
            user_question=user_question,
            assistant_answer=assistant_answer,
            latency=latency,
            token_count=token_count,
            created_at=now
        )
        db.session.add(message)

        # Update session activity timestamp
        session.updated_at = now

        # Automatic Title Generation on first turn if title is default
        if session.title == DEFAULT_SESSION_TITLE or not session.title or session.title == "Research Discussion":
            auto_title = generate_session_title(user_question)
            session.title = auto_title
            logger.info(f"Automatically generated title for session UUID='{session.session_uuid}': '{auto_title}'")

        db.session.commit()
        logger.info(f"Appended Message turn ID={message.id} to session ID={session.id}")
        return message, session
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Failed to append message turn to session '{session_id_or_uuid}': {e}")
        raise RuntimeError(f"Message append transaction failed: {str(e)}") from e

def format_multi_turn_history(session_id_or_uuid: str, max_turns: int = 10) -> List[Dict[str, str]]:
    """
    Formats previous Q&A turns of a session into a context list for LLM multi-turn memory.

    Args:
        session_id_or_uuid (str): Session UUID or ID.
        max_turns (int): Maximum number of recent turns to retrieve.

    Returns:
        List[Dict[str, str]]: Ordered conversation turns [{"role": "user", "content": ...}, ...]
    """
    session = get_session(session_id_or_uuid)
    if not session or not session.messages:
        return []

    messages = session.messages[-max_turns:]
    history = []

    for msg in messages:
        if msg.user_question:
            history.append({"role": "user", "content": msg.user_question})
        if msg.assistant_answer:
            history.append({"role": "assistant", "content": msg.assistant_answer})

    return history
