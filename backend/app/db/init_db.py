import bcrypt
from sqlalchemy import select, text

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import SessionLocal, get_engine
from app.models.chat import ChatMessage, ChatSession
from app.models.document import Document, DocumentChunk, DocumentEmbedding
from app.models.user import User


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def init_db() -> None:
    settings = get_settings()
    engine = get_engine()

    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.create_all(
            bind=connection,
            tables=[
                User.__table__,
                ChatSession.__table__,
                ChatMessage.__table__,
                Document.__table__,
                DocumentChunk.__table__,
                DocumentEmbedding.__table__,
            ],
        )

    with SessionLocal() as db:
        existing_user = db.scalar(
            select(User).where(User.username == settings.initial_user_username)
        )
        if existing_user is not None:
            return

        db.add(
            User(
                username=settings.initial_user_username,
                password_hash=_hash_password(settings.initial_user_password),
            )
        )
        db.commit()
