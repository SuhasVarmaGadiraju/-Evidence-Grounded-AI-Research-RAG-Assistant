from datetime import datetime, timezone
from database.database import db

def utc_now():
    return datetime.now(timezone.utc)

class User(db.Model):
    """
    User model storing user profiles authenticated via Firebase Auth.
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    firebase_uid = db.Column(db.String(255), unique=True, index=True, nullable=False)
    name = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), unique=True, index=True, nullable=False)
    photo_url = db.Column(db.Text, nullable=True)
    provider = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    last_login = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relationships
    documents = db.relationship("Document", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User id={self.id} firebase_uid='{self.firebase_uid}' email='{self.email}'>"

    def to_dict(self):
        return {
            "id": self.id,
            "firebase_uid": self.firebase_uid,
            "name": self.name,
            "email": self.email,
            "photo_url": self.photo_url,
            "provider": self.provider,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
