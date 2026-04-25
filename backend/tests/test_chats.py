from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes.chats import get_nvidia_client
from app.core.config import get_settings
from app.core.security import AUTH_COOKIE_NAME, create_access_token
from app.db.session import get_db
from app.main import create_app
from app.models.chat import ChatMessage, ChatRole, ChatSession
from app.models.document import Document, DocumentChunk, DocumentEmbedding, DocumentStatus
from app.models.user import User
from app.schemas.chat import ChatRequest
from app.services.rag import build_no_context_response


@pytest.fixture(autouse=True)
def configured_settings(monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    monkeypatch.setenv("APP_DOMAIN", "ai.example.com")
    monkeypatch.setenv("LETSENCRYPT_EMAIL", "admin@example.com")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.setenv("INITIAL_USER_USERNAME", "tester")
    monkeypatch.setenv("INITIAL_USER_PASSWORD", "correct-password")
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test")
    monkeypatch.setenv("NVIDIA_EMBEDDING_MODEL", "embed")
    monkeypatch.setenv("NVIDIA_LLM_MODEL", "gemma")
    monkeypatch.setenv("BACKEND_CORS_ORIGINS", "")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


class FakeNvidiaClient:
    def __init__(self, response: str = "Assistant answer", failure: Exception | None = None) -> None:
        self.response = response
        self.failure = failure
        self.embedded_texts: list[str] = []
        self.messages: list[list[dict[str, str]]] = []

    def embed(self, text: str) -> list[float]:
        self.embedded_texts.append(text)
        return [1.0] + [0.0] * 1023

    def chat(self, messages: list[dict[str, str]]) -> str:
        self.messages.append(messages)
        if self.failure is not None:
            raise self.failure
        return self.response


def test_chat_request_defaults_to_normal_mode_and_concise_style() -> None:
    payload = ChatRequest(message="Hello")

    assert payload.mode == "normal"
    assert payload.style == "concise"


def test_list_chats_requires_authentication() -> None:
    client, _session_local, _fake_client = _client_with_user()

    response = client.get("/api/chats")

    assert response.status_code == 401


def test_create_and_list_chats_for_current_user() -> None:
    client, session_local, _fake_client = _client_with_user()
    token = create_access_token("1")

    create_response = client.post("/api/chats", headers={"cookie": f"{AUTH_COOKIE_NAME}={token}"})

    assert create_response.status_code == 200
    assert create_response.json()["title"] == "New chat"

    with session_local() as db:
        other_user = User(username="other", password_hash="hash")
        db.add(other_user)
        db.flush()
        db.add(ChatSession(user_id=other_user.id, title="Other chat"))
        db.commit()

    list_response = client.get("/api/chats", headers={"cookie": f"{AUTH_COOKIE_NAME}={token}"})

    assert list_response.status_code == 200
    assert list_response.json() == [{"id": create_response.json()["id"], "title": "New chat"}]


def test_send_normal_message_persists_messages_and_uses_fake_client() -> None:
    client, session_local, fake_client = _client_with_user(client_response="Normal answer")
    token = create_access_token("1")
    session_id = _create_session(session_local, user_id=1)

    response = client.post(
        f"/api/chats/{session_id}/messages",
        headers={"cookie": f"{AUTH_COOKIE_NAME}={token}"},
        json={"message": "Summarize this", "mode": "normal", "style": "detailed"},
    )

    assert response.status_code == 200
    assert response.json()["message"]["content"] == "Normal answer"
    assert response.json()["message"]["role"] == ChatRole.ASSISTANT
    assert fake_client.messages == [
        [
            {
                "role": "system",
                "content": "Respond in a detailed style for an internal company assistant.",
            },
            {"role": "user", "content": "Summarize this"},
        ]
    ]

    with session_local() as db:
        messages = db.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at, ChatMessage.id)
        ).all()

    assert [(message.role, message.content) for message in messages] == [
        (ChatRole.USER, "Summarize this"),
        (ChatRole.ASSISTANT, "Normal answer"),
    ]


def test_send_normal_message_accepts_expert_style() -> None:
    client, _session_local, fake_client = _client_with_user(client_response="Expert answer")
    token = create_access_token("1")
    session_id = _create_session(_session_local, user_id=1)

    response = client.post(
        f"/api/chats/{session_id}/messages",
        headers={"cookie": f"{AUTH_COOKIE_NAME}={token}"},
        json={"message": "Explain this architecture", "mode": "normal", "style": "expert"},
    )

    assert response.status_code == 200
    assert response.json()["message"]["content"] == "Expert answer"
    assert fake_client.messages[0][0] == {
        "role": "system",
        "content": "Respond in an expert style for an internal company assistant.",
    }


def test_send_normal_message_failure_returns_safe_error_and_keeps_user_message() -> None:
    client, session_local, _fake_client = _client_with_user(
        client_failure=RuntimeError("provider unavailable"),
        raise_server_exceptions=False,
    )
    token = create_access_token("1")
    session_id = _create_session(session_local, user_id=1)

    response = client.post(
        f"/api/chats/{session_id}/messages",
        headers={"cookie": f"{AUTH_COOKIE_NAME}={token}"},
        json={"message": "Will this persist?", "mode": "normal"},
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Chat response failed"}

    with session_local() as db:
        messages = db.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at, ChatMessage.id)
        ).all()

    assert [(message.role, message.content) for message in messages] == [
        (ChatRole.USER, "Will this persist?"),
    ]


def test_send_rag_message_without_context_persists_grounded_response() -> None:
    client, session_local, fake_client = _client_with_user()
    token = create_access_token("1")
    session_id = _create_session(session_local, user_id=1)

    response = client.post(
        f"/api/chats/{session_id}/messages",
        headers={"cookie": f"{AUTH_COOKIE_NAME}={token}"},
        json={"message": "What is the policy?", "mode": "rag"},
    )

    assert response.status_code == 200
    assert response.json()["message"]["content"] == build_no_context_response()
    assert fake_client.messages == []

    with session_local() as db:
        messages = db.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at, ChatMessage.id)
        ).all()

    assert [(message.role, message.content) for message in messages] == [
        (ChatRole.USER, "What is the policy?"),
        (ChatRole.ASSISTANT, build_no_context_response()),
    ]


def test_send_rag_message_uses_ready_document_context() -> None:
    client, session_local, fake_client = _client_with_user(client_response="Grounded answer")
    token = create_access_token("1")
    session_id = _create_session(session_local, user_id=1)
    _create_ready_document_chunk(session_local, user_id=1)

    response = client.post(
        f"/api/chats/{session_id}/messages",
        headers={"cookie": f"{AUTH_COOKIE_NAME}={token}"},
        json={"message": "What is the policy?", "mode": "rag", "style": "expert"},
    )

    assert response.status_code == 200
    assert response.json()["message"]["content"] == "Grounded answer"
    assert response.json()["message"]["source_summary"] == "handbook.md"
    assert fake_client.embedded_texts == ["What is the policy?"]
    assert fake_client.messages == [
        [
            {
                "role": "system",
                "content": (
                    "Answer using only the provided company document context. "
                    "Use the requested style: expert."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Context:\nSource: handbook.md\nTravel requires approval."
                    "\n\nQuestion:\nWhat is the policy?"
                ),
            },
        ]
    ]


def test_send_message_rejects_chat_owned_by_another_user() -> None:
    client, session_local, _fake_client = _client_with_user()
    token = create_access_token("1")

    with session_local() as db:
        other_user = User(username="other", password_hash="hash")
        db.add(other_user)
        db.flush()
        other_session = ChatSession(user_id=other_user.id, title="Other chat")
        db.add(other_session)
        db.commit()
        session_id = other_session.id

    response = client.post(
        f"/api/chats/{session_id}/messages",
        headers={"cookie": f"{AUTH_COOKIE_NAME}={token}"},
        json={"message": "Hello"},
    )

    assert response.status_code == 404


def _client_with_user(
    *,
    client_response: str = "Assistant answer",
    client_failure: Exception | None = None,
    raise_server_exceptions: bool = True,
) -> tuple[TestClient, sessionmaker[Session], FakeNvidiaClient]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    User.__table__.create(bind=engine)
    ChatSession.__table__.create(bind=engine)
    ChatMessage.__table__.create(bind=engine)
    Document.__table__.create(bind=engine)
    DocumentChunk.__table__.create(bind=engine)
    DocumentEmbedding.__table__.create(bind=engine)

    with testing_session_local() as db:
        db.add(User(username="tester", password_hash="hash"))
        db.commit()

    app = create_app()
    fake_client = FakeNvidiaClient(client_response, client_failure)

    def override_get_db() -> Generator[Session]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_nvidia_client] = lambda: fake_client
    return (
        TestClient(app, raise_server_exceptions=raise_server_exceptions),
        testing_session_local,
        fake_client,
    )


def _create_session(session_local: sessionmaker[Session], *, user_id: int) -> int:
    with session_local() as db:
        session = ChatSession(user_id=user_id, title="New chat")
        db.add(session)
        db.commit()
        return session.id


def _create_ready_document_chunk(session_local: sessionmaker[Session], *, user_id: int) -> None:
    with session_local() as db:
        document = Document(
            user_id=user_id,
            filename="handbook.md",
            content_type="text/markdown",
            status=DocumentStatus.READY,
        )
        db.add(document)
        db.flush()
        chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=0,
            content="Travel requires approval.",
        )
        db.add(chunk)
        db.flush()
        db.add(DocumentEmbedding(chunk_id=chunk.id, embedding=[1.0] + [0.0] * 1023))
        db.commit()
