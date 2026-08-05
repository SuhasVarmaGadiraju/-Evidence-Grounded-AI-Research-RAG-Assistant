import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from database.database import db
from database.models.user import User

logger = logging.getLogger("rag_backend.services.user_service")

def sync_user_profile(user_data: Dict[str, Any]) -> User:
    """
    Synchronizes Firebase authenticated user profile into PostgreSQL.
    Performs an upsert to create user if not present or update metadata/last_login if existing.

    Args:
        user_data (Dict[str, Any]): Dictionary containing user attributes:
            - firebase_uid (str): Unique identifier from Firebase.
            - email (str): User email address.
            - name (Optional[str]): Display name.
            - photo_url (Optional[str]): Avatar/Profile photo URL.
            - provider (Optional[str]): Auth provider (google.com, password, etc.).

    Returns:
        User: Updated or created User ORM instance.

    Raises:
        ValueError: If firebase_uid or email is missing.
        RuntimeError: If database transaction fails.
    """
    firebase_uid: Optional[str] = user_data.get("firebase_uid") or user_data.get("uid") or user_data.get("id")
    email: Optional[str] = user_data.get("email")

    if not firebase_uid or not email:
        logger.error("User sync failed: 'firebase_uid' and 'email' are required fields.")
        raise ValueError("Both 'firebase_uid' and 'email' are required for user synchronization.")

    name: Optional[str] = user_data.get("name") or user_data.get("displayName")
    photo_url: Optional[str] = user_data.get("photo_url") or user_data.get("avatarUrl") or user_data.get("photoURL")
    provider: Optional[str] = user_data.get("provider") or "firebase"
    now: datetime = datetime.now(timezone.utc)

    try:
        # Search by firebase_uid or email
        user: Optional[User] = User.query.filter(
            (User.firebase_uid == firebase_uid) | (User.email == email)
        ).first()

        if user:
            logger.info(f"Existing user found for UID '{firebase_uid}'. Updating last_login and profile metadata.")
            user.firebase_uid = firebase_uid
            user.email = email
            if name:
                user.name = name
            if photo_url:
                user.photo_url = photo_url
            if provider:
                user.provider = provider
            user.last_login = now
        else:
            logger.info(f"Creating new user record for UID '{firebase_uid}' ({email}).")
            user = User(
                firebase_uid=firebase_uid,
                email=email,
                name=name,
                photo_url=photo_url,
                provider=provider,
                created_at=now,
                last_login=now
            )
            db.session.add(user)

        db.session.commit()
        logger.info(f"User synchronization successful for user ID {user.id} ({user.email}).")
        return user

    except Exception as e:
        db.session.rollback()
        logger.exception(f"Database error during user synchronization for UID '{firebase_uid}': {e}")
        raise RuntimeError(f"User synchronization transaction failed: {str(e)}") from e
