from collections.abc import Generator

import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.security import AUTH_COOKIE_NAME, create_access_token
from app.db import session as session_module
from app.db.session import get_db
from app.main import create_app
from app.models.document import Document, DocumentChunk, DocumentEmbedding, DocumentStatus
from app.models.user import User
from app.services.document_parser import UnsupportedDocumentType, extract_text
from app.services.indexing import index_document


@pytest.fixture
def configured_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_DOMAIN", "ai.example.com")
    monkeypatch.setenv("LETSENCRYPT_EMAIL", "admin@example.com")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.setenv("INITIAL_USER_USERNAME", "tester")
    monkeypatch.setenv("INITIAL_USER_PASSWORD", "correct-password")
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test")
    monkeypatch.setenv("NVIDIA_EMBEDDING_MODEL", "embed")
    monkeypatch.setenv("NVIDIA_LLM_MODEL", "gemma")
    monkeypatch.setenv("UPLOAD_MAX_MB", "1")
    monkeypatch.setenv("BACKEND_CORS_ORIGINS", "")
    monkeypatch.setattr("app.services.indexing._default_embedding_provider", lambda text: [0.1] * 1024)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_extract_text_from_txt_bytes() -> None:
    assert extract_text("notes.txt", b"hello world") == "hello world"


def test_extract_text_from_md_bytes() -> None:
    assert extract_text("notes.md", b"# Heading\n\nhello") == "# Heading\n\nhello"


def test_extract_text_rejects_unknown_extension() -> None:
    try:
        extract_text("archive.zip", b"data")
    except UnsupportedDocumentType as exc:
        assert "Unsupported file type" in str(exc)
    else:
        raise AssertionError("UnsupportedDocumentType was not raised")


def test_index_document_stores_embeddings_with_injected_provider(configured_settings: None) -> None:
    _client, session_local = _client_with_user()
    embedded_texts: list[str] = []

    with session_local() as db:
        document = Document(user_id=1, filename="notes.txt", content_type="text/plain")
        db.add(document)
        db.commit()
        document_id = document.id

    def fake_embed(text: str) -> list[float]:
        embedded_texts.append(text)
        return [0.1] * 1024

    index_document(document_id, "notes.txt", b"alpha " * 300, embedding_provider=fake_embed)

    with session_local() as db:
        document = db.get(Document, document_id)
        assert document is not None
        chunks = db.scalars(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        ).all()
        embeddings = db.scalars(
            select(DocumentEmbedding).join(DocumentChunk).where(DocumentChunk.document_id == document_id)
        ).all()

    assert document.status == DocumentStatus.READY
    assert len(chunks) > 1
    assert len(embeddings) == len(chunks)
    assert embedded_texts == [chunk.content for chunk in chunks]


def test_upload_document_requires_authentication(configured_settings: None) -> None:
    client, _session_local = _client_with_user()

    response = client.post(
        "/api/documents",
        files={"file": ("notes.txt", b"hello world", "text/plain")},
    )

    assert response.status_code == 401


def test_upload_document_indexes_text_for_authenticated_user(configured_settings: None) -> None:
    client, session_local = _client_with_user()
    token = create_access_token("1")

    response = client.post(
        "/api/documents",
        files={"file": ("notes.txt", b"alpha " * 300, "text/plain")},
        headers={"cookie": f"{AUTH_COOKIE_NAME}={token}"},
    )

    assert response.status_code == 200
    assert response.json()["filename"] == "notes.txt"
    assert response.json()["status"] == DocumentStatus.UPLOADED

    with session_local() as db:
        document = db.scalar(select(Document).where(Document.filename == "notes.txt"))
        assert document is not None
        assert document.user_id == 1
        assert document.status == DocumentStatus.READY
        assert document.storage_path is not None
        chunks = db.scalars(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document.id)
            .order_by(DocumentChunk.chunk_index)
        ).all()

    assert len(chunks) > 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].content.startswith("alpha")


def test_upload_document_rejects_unsupported_extension(configured_settings: None) -> None:
    client, _session_local = _client_with_user()
    token = create_access_token("1")

    response = client.post(
        "/api/documents",
        files={"file": ("archive.zip", b"data", "application/zip")},
        headers={"cookie": f"{AUTH_COOKIE_NAME}={token}"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Unsupported file type: .zip"}


def test_list_documents_returns_current_user_documents(configured_settings: None) -> None:
    client, session_local = _client_with_user()
    token = create_access_token("1")

    with session_local() as db:
        db.add(Document(user_id=1, filename="old.txt", content_type="text/plain"))
        db.add(Document(user_id=1, filename="new.txt", content_type="text/plain"))
        db.add(User(username="other", password_hash="hash"))
        db.flush()
        db.add(Document(user_id=2, filename="other.txt", content_type="text/plain"))
        db.commit()

    response = client.get("/api/documents", headers={"cookie": f"{AUTH_COOKIE_NAME}={token}"})

    assert response.status_code == 200
    assert [document["filename"] for document in response.json()] == ["new.txt", "old.txt"]


def _client_with_user() -> tuple[TestClient, sessionmaker[Session]]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session_module.SessionLocal.configure(bind=engine)
    User.__table__.create(bind=engine)
    Document.__table__.create(bind=engine)
    DocumentChunk.__table__.create(bind=engine)
    DocumentEmbedding.__table__.create(bind=engine)

    password_hash = bcrypt.hashpw(b"correct-password", bcrypt.gensalt()).decode("utf-8")
    with testing_session_local() as db:
        db.add(User(username="tester", password_hash=password_hash))
        db.commit()

    app = create_app()

    def override_get_db() -> Generator[Session]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), testing_session_local
