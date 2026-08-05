from datetime import datetime, timezone
from database.database import db

def utc_now() -> datetime:
    """Returns timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)

class Message(db.Model):
    """
    Message model representing a single conversational Q&A turn or system event within a research session.
    Stores the user prompt, assistant response, execution metrics, and links to chunk retrieval logs.
    """
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    message_uuid = db.Column(db.String(36), unique=True, index=True, nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey("research_sessions.id", ondelete="CASCADE"), index=True, nullable=False)
    role = db.Column(db.String(50), default="user", nullable=False)
    user_question = db.Column(db.Text, nullable=True)
    assistant_answer = db.Column(db.Text, nullable=True)
    latency = db.Column(db.Float, default=0.0, nullable=False)
    token_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    session = db.relationship("ResearchSession", back_populates="messages")
    retrieval_logs = db.relationship("RetrievalLog", back_populates="message", cascade="all, delete-orphan", order_by="RetrievalLog.id.asc()")

    def __repr__(self) -> str:
        return f"<Message id={self.id} uuid='{self.message_uuid}' role='{self.role}' session_id={self.session_id}>"

    def to_dict(self, include_logs: bool = True) -> dict:
        """
        Serializes Message instance into a JSON-compatible dictionary.

        Args:
            include_logs (bool): If True, includes serialized retrieval logs and score breakdowns.

        Returns:
            dict: Serialized message dictionary.
        """
        data = {
            "id": self.id,
            "message_id": self.message_uuid,
            "message_uuid": self.message_uuid,
            "session_id": self.session.session_uuid if self.session else self.session_id,
            "role": self.role,
            "user_question": self.user_question,
            "assistant_answer": self.assistant_answer,
            "latency": round(self.latency, 3),
            "token_count": self.token_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_logs:
            data["retrieval_logs"] = [log.to_dict() for log in self.retrieval_logs]
        return data
