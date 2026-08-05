from datetime import datetime, timezone
from database.database import db

def utc_now() -> datetime:
    """Returns timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)

class ResearchSession(db.Model):
    """
    ResearchSession model representing a persistent conversation workspace session.
    Groups chat turns (messages) and fine-grained retrieval attribution logs under a session thread.
    """
    __tablename__ = "research_sessions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_uuid = db.Column(db.String(36), unique=True, index=True, nullable=False)
    title = db.Column(db.String(255), default="New Research Session", nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    user = db.relationship("User", back_populates="research_sessions")
    messages = db.relationship("Message", back_populates="session", cascade="all, delete-orphan", order_by="Message.created_at.asc()")

    def __repr__(self) -> str:
        return f"<ResearchSession id={self.id} uuid='{self.session_uuid}' title='{self.title}'>"

    def to_dict(self, include_messages: bool = False) -> dict:
        """
        Serializes ResearchSession instance into a JSON-compatible dictionary.

        Args:
            include_messages (bool): If True, embeds all serialized child messages.

        Returns:
            dict: Serialized session dictionary.
        """
        data = {
            "id": self.id,
            "session_id": self.session_uuid,
            "session_uuid": self.session_uuid,
            "title": self.title,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "message_count": len(self.messages) if self.messages else 0
        }
        if include_messages:
            data["messages"] = [msg.to_dict(include_logs=True) for msg in self.messages]
        return data
