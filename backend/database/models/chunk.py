from datetime import datetime, timezone
from database.database import db

def utc_now():
    return datetime.now(timezone.utc)

class Chunk(db.Model):
    """
    Chunk model storing text metadata and FAISS vector indices.
    Vector embeddings are stored separately in FAISS.
    """
    __tablename__ = "chunks"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    chunk_uuid = db.Column(db.String(36), unique=True, index=True, nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    page_number = db.Column(db.Integer, default=1, nullable=False)
    chunk_index = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    faiss_vector_id = db.Column(db.BigInteger, index=True, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    document = db.relationship("Document", back_populates="chunks")

    def __repr__(self):
        return f"<Chunk id={self.id} uuid='{self.chunk_uuid}' doc_id={self.document_id} page={self.page_number} index={self.chunk_index}>"

    def to_dict(self):
        return {
            "id": self.id,
            "chunk_uuid": self.chunk_uuid,
            "document_id": self.document_id,
            "page_number": self.page_number,
            "chunk_index": self.chunk_index,
            "text": self.text,
            "faiss_vector_id": self.faiss_vector_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
