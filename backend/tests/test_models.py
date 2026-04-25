from sqlalchemy import DateTime

from app.models.chat import ChatMessage, ChatRole, ChatSession
from app.models.document import Document, DocumentChunk, DocumentEmbedding, DocumentStatus
from app.models.user import User


def test_models_can_be_constructed() -> None:
    user = User(username="tester", password_hash="hash")
    session = ChatSession(title="New chat", user=user)
    message = ChatMessage(session=session, role=ChatRole.USER, content="Hello")
    document = Document(user=user, filename="policy.pdf", content_type="application/pdf")
    chunk = DocumentChunk(document=document, chunk_index=0, content="Policy text", source_locator="p. 1")

    assert user.username == "tester"
    assert session.title == "New chat"
    assert message.role == ChatRole.USER
    assert message.created_at is None
    assert document.status == DocumentStatus.UPLOADED
    assert chunk.source_locator == "p. 1"


def test_model_tables_expose_durable_relationship_metadata() -> None:
    assert DocumentEmbedding.__table__.c.chunk_id.unique is True
    assert isinstance(ChatMessage.__table__.c.created_at.type, DateTime)
    assert ChatMessage.__table__.c.created_at.nullable is False
    assert DocumentChunk.__table__.c.source_locator.nullable is True

    assert _foreign_key_ondelete(ChatSession, "user_id") == "CASCADE"
    assert _foreign_key_ondelete(ChatMessage, "session_id") == "CASCADE"
    assert _foreign_key_ondelete(Document, "user_id") == "CASCADE"
    assert _foreign_key_ondelete(DocumentChunk, "document_id") == "CASCADE"
    assert _foreign_key_ondelete(DocumentEmbedding, "chunk_id") == "CASCADE"


def test_chat_session_messages_have_deterministic_ordering() -> None:
    assert tuple(ChatSession.messages.property.order_by) == (
        ChatMessage.created_at,
        ChatMessage.id,
    )


def _foreign_key_ondelete(model: type, column_name: str) -> str | None:
    [foreign_key] = model.__table__.c[column_name].foreign_keys
    return foreign_key.ondelete
