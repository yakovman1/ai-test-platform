from app.models.chat import ChatMessage, ChatRole, ChatSession
from app.models.document import Document, DocumentStatus
from app.models.user import User


def test_models_can_be_constructed() -> None:
    user = User(username="tester", password_hash="hash")
    session = ChatSession(title="New chat", user=user)
    message = ChatMessage(session=session, role=ChatRole.USER, content="Hello")
    document = Document(user=user, filename="policy.pdf", content_type="application/pdf")

    assert user.username == "tester"
    assert session.title == "New chat"
    assert message.role == ChatRole.USER
    assert document.status == DocumentStatus.UPLOADED
