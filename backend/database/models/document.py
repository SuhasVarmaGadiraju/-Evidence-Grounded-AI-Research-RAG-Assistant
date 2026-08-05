from datetime import datetime, timezone
from database.database import db

def utc_now():
    return datetime.now(timezone.utc)

# Valid document statuses as required
VALID_DOCUMENT_STATUSES = [
    "Queued",
    "Uploading",
    "Extracting",
    "Cleaning",
    "Chunking",
    "Embedding",
    "Indexed",
    "Completed",
    "Failed"
]

class Document(db.Model):
    """
    Document model storing PDF metadata and processing state.
    """
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    document_uuid = db.Column(db.String(36), unique=True, index=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(512), nullable=False)
    pages = db.Column(db.Integer, default=0, nullable=False)
    file_size = db.Column(db.BigInteger, default=0, nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"), index=True, nullable=True)
    status = db.Column(db.String(50), default="Queued", nullable=False)
    chunk_count = db.Column(db.Integer, default=0, nullable=False)
    embedding_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    user = db.relationship("User", back_populates="documents")
    chunks = db.relationship("Chunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document id={self.id} uuid='{self.document_uuid}' title='{self.title}' status='{self.status}'>"

    def to_dict(self):
        return {
            "id": self.id,
            "document_uuid": self.document_uuid,
            "title": self.title,
            "filename": self.filename,
            "filepath": self.filepath,
            "pages": self.pages,
            "file_size": self.file_size,
            "uploaded_by": self.uploaded_by,
            "status": self.status,
            "chunk_count": self.chunk_count,
            "embedding_count": self.embedding_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
