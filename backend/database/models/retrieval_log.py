from datetime import datetime, timezone
from database.database import db

def utc_now() -> datetime:
    """Returns timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)

class RetrievalLog(db.Model):
    """
    RetrievalLog model capturing fine-grained evidence attribution for an assistant answer turn.
    Stores document/chunk locations, FAISS vector indices, retrieval rank, strategy,
    and the full 4-score retrieval breakdown (Semantic cosine similarity, BM25 lexical score,
    RRF rank fusion, Cross-Encoder reranker score).
    """
    __tablename__ = "retrieval_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    message_id = db.Column(db.Integer, db.ForeignKey("messages.id", ondelete="CASCADE"), index=True, nullable=False)
    document_uuid = db.Column(db.String(36), index=True, nullable=False)
    chunk_uuid = db.Column(db.String(255), index=True, nullable=False)
    page_number = db.Column(db.Integer, default=1, nullable=False)
    faiss_vector_id = db.Column(db.BigInteger, nullable=True)
    semantic_score = db.Column(db.Float, default=0.0, nullable=False)
    bm25_score = db.Column(db.Float, default=0.0, nullable=False)
    rrf_score = db.Column(db.Float, default=0.0, nullable=False)
    reranker_score = db.Column(db.Float, default=0.0, nullable=False)
    retrieval_strategy = db.Column(db.String(50), default="Hybrid RRF", nullable=False)
    retrieval_rank = db.Column(db.Integer, default=1, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    message = db.relationship("Message", back_populates="retrieval_logs")

    def __repr__(self) -> str:
        return (
            f"<RetrievalLog id={self.id} msg_id={self.message_id} "
            f"doc_uuid='{self.document_uuid}' chunk_uuid='{self.chunk_uuid}' "
            f"strategy='{self.retrieval_strategy}' rank={self.retrieval_rank}>"
        )

    def to_dict(self) -> dict:
        """
        Serializes RetrievalLog instance into a JSON-compatible dictionary.

        Returns:
            dict: Serialized retrieval log entry with score breakdown and rank metadata.
        """
        return {
            "id": self.id,
            "message_id": self.message_id,
            "document_uuid": self.document_uuid,
            "chunk_uuid": self.chunk_uuid,
            "page_number": self.page_number,
            "faiss_vector_id": self.faiss_vector_id,
            "semantic_score": round(self.semantic_score, 4),
            "bm25_score": round(self.bm25_score, 4),
            "rrf_score": round(self.rrf_score, 4),
            "reranker_score": round(self.reranker_score, 4),
            "retrieval_strategy": self.retrieval_strategy,
            "retrieval_rank": self.retrieval_rank,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
