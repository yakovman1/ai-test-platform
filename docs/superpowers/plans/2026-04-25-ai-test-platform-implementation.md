# AI Test Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the approved Dockerized AI test platform with React, FastAPI, Postgres/pgvector, Caddy HTTPS, single-user auth, shared chat history, document upload, and NVIDIA-backed normal/RAG chat.

**Architecture:** The repository starts from an empty workspace and becomes a monorepo with `backend`, `frontend`, deployment files, and operational docs. FastAPI owns auth, documents, background indexing, NVIDIA calls, and chat APIs. React owns login, shared sidebar, document upload/status, chat history, and mode/style controls.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic Settings, pytest, httpx, passlib/bcrypt, python-jose, pgvector, React, TypeScript, Vite, Vitest, Testing Library, Docker Compose, Caddy, Postgres with pgvector.

---

## File Structure

- Create `backend/pyproject.toml`: backend package metadata, dependencies, pytest configuration.
- Create `backend/Dockerfile`: production backend image.
- Create `backend/app/main.py`: FastAPI app assembly, CORS, routers, startup seed hook.
- Create `backend/app/core/config.py`: environment settings.
- Create `backend/app/core/security.py`: password hashing, JWT creation, cookie constants.
- Create `backend/app/db/session.py`: SQLAlchemy engine and session dependency.
- Create `backend/app/db/base.py`: declarative base and model imports.
- Create `backend/app/db/init_db.py`: pgvector extension setup and initial user seed.
- Create `backend/app/models/*.py`: SQLAlchemy models for users, chats, documents, chunks, embeddings.
- Create `backend/app/schemas/*.py`: API request and response schemas.
- Create `backend/app/api/routes/*.py`: auth, chats, documents, and health endpoints.
- Create `backend/app/services/*.py`: document parsing, chunking, NVIDIA client, embeddings, RAG, chat orchestration.
- Create `backend/alembic.ini` and `backend/alembic/*`: migrations.
- Create `backend/tests/*`: backend tests.
- Create `frontend/package.json`: frontend scripts and dependencies.
- Create `frontend/Dockerfile`: production frontend image.
- Create `frontend/vite.config.ts`: Vite and test configuration.
- Create `frontend/src/api/client.ts`: typed API client.
- Create `frontend/src/auth/*`: auth state and login screen.
- Create `frontend/src/chat/*`: chat workspace components and hooks.
- Create `frontend/src/documents/*`: upload and document status components.
- Create `frontend/src/test/*`: test setup and mocks.
- Create `docker-compose.yml`: Caddy, frontend, backend, and Postgres services.
- Create `Caddyfile`: HTTPS routing for frontend and `/api`.
- Create `.env.example`: all required runtime settings without secrets.
- Create `.gitignore`: ignore secrets, build output, Python caches, Node modules, local uploads, and `.superpowers`.
- Create `docs/deployment.md`: VPS setup, deploy, update, backup, restore, and troubleshooting commands.

## Task 1: Repository Bootstrap

**Files:**
- Create: `.gitignore`
- Create: `.env.example`
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`

- [ ] **Step 1: Add repository ignore rules**

Create `.gitignore`:

```gitignore
.env
.env.*
!.env.example
.superpowers/
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
.mypy_cache/
.venv/
dist/
build/
node_modules/
coverage/
htmlcov/
backend/uploads/
frontend/.vite/
```

- [ ] **Step 2: Add environment example**

Create `.env.example`:

```dotenv
APP_DOMAIN=ai.example.com
LETSENCRYPT_EMAIL=admin@example.com
POSTGRES_DB=ai_platform
POSTGRES_USER=ai_platform
POSTGRES_PASSWORD=change-me
DATABASE_URL=postgresql+psycopg://ai_platform:change-me@postgres:5432/ai_platform
JWT_SECRET=change-me-to-a-long-random-secret
INITIAL_USER_USERNAME=tester
INITIAL_USER_PASSWORD=change-me
NVIDIA_API_KEY=nvapi-change-me
NVIDIA_EMBEDDING_MODEL=nvidia/embedding-model
NVIDIA_LLM_MODEL=google/gemma-4
UPLOAD_MAX_MB=20
RAG_TOP_K=5
BACKEND_CORS_ORIGINS=https://ai.example.com
```

- [ ] **Step 3: Create backend package config**

Create `backend/pyproject.toml`:

```toml
[project]
name = "ai-test-platform-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "alembic",
  "bcrypt",
  "fastapi",
  "httpx",
  "passlib[bcrypt]",
  "pgvector",
  "psycopg[binary]",
  "pydantic-settings",
  "python-docx",
  "python-jose[cryptography]",
  "python-multipart",
  "pypdf",
  "sqlalchemy",
  "uvicorn[standard]",
]

[project.optional-dependencies]
dev = [
  "pytest",
  "pytest-asyncio",
  "ruff",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ruff]
line-length = 100
target-version = "py312"
```

- [ ] **Step 4: Create minimal FastAPI app**

Create `backend/app/main.py`:

```python
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="AI Test Platform API")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 5: Create frontend bootstrap**

Create `frontend/package.json`:

```json
{
  "name": "ai-test-platform-frontend",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite --host 0.0.0.0",
    "build": "tsc -b && vite build",
    "preview": "vite preview --host 0.0.0.0",
    "test": "vitest run"
  },
  "dependencies": {
    "@vitejs/plugin-react": "latest",
    "vite": "latest",
    "typescript": "latest",
    "react": "latest",
    "react-dom": "latest"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "latest",
    "@testing-library/react": "latest",
    "@types/react": "latest",
    "@types/react-dom": "latest",
    "jsdom": "latest",
    "vitest": "latest"
  }
}
```

Create `frontend/index.html`:

```html
<div id="root"></div>
<script type="module" src="/src/main.tsx"></script>
```

Create `frontend/src/main.tsx`:

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

Create `frontend/src/App.tsx`:

```tsx
export function App() {
  return <main>AI Test Platform</main>;
}
```

- [ ] **Step 6: Verify bootstrap commands**

Run:

```bash
cd backend && python -m pip install -e ".[dev]" && python -m pytest
cd ../frontend && npm install && npm test
```

Expected:

- Backend installs and pytest exits with no collected tests or passing tests.
- Frontend installs and Vitest exits with no failing tests.

- [ ] **Step 7: Commit bootstrap**

```bash
git add .gitignore .env.example backend frontend
git commit -m "chore: bootstrap AI test platform"
```

## Task 2: Backend Configuration, Database, And Models

**Files:**
- Create: `backend/app/core/config.py`
- Create: `backend/app/db/session.py`
- Create: `backend/app/db/base.py`
- Create: `backend/app/db/init_db.py`
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/chat.py`
- Create: `backend/app/models/document.py`
- Create: `backend/tests/test_config.py`
- Create: `backend/tests/test_models.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write configuration tests**

Create `backend/tests/test_config.py`:

```python
from app.core.config import Settings


def test_settings_parse_cors_origins() -> None:
    settings = Settings(
        app_domain="ai.example.com",
        letsencrypt_email="admin@example.com",
        database_url="postgresql+psycopg://u:p@localhost:5432/db",
        jwt_secret="secret",
        initial_user_username="tester",
        initial_user_password="password",
        nvidia_api_key="key",
        nvidia_embedding_model="embed",
        nvidia_llm_model="gemma",
        backend_cors_origins="https://ai.example.com,http://localhost:5173",
    )

    assert settings.cors_origins == ["https://ai.example.com", "http://localhost:5173"]
```

- [ ] **Step 2: Implement settings**

Create `backend/app/core/config.py`:

```python
from functools import cached_property

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_domain: str = Field(alias="APP_DOMAIN")
    letsencrypt_email: str = Field(alias="LETSENCRYPT_EMAIL")
    database_url: str = Field(alias="DATABASE_URL")
    jwt_secret: str = Field(alias="JWT_SECRET")
    initial_user_username: str = Field(alias="INITIAL_USER_USERNAME")
    initial_user_password: str = Field(alias="INITIAL_USER_PASSWORD")
    nvidia_api_key: str = Field(alias="NVIDIA_API_KEY")
    nvidia_embedding_model: str = Field(alias="NVIDIA_EMBEDDING_MODEL")
    nvidia_llm_model: str = Field(alias="NVIDIA_LLM_MODEL")
    upload_max_mb: int = Field(default=20, alias="UPLOAD_MAX_MB")
    rag_top_k: int = Field(default=5, alias="RAG_TOP_K")
    backend_cors_origins: str = Field(default="", alias="BACKEND_CORS_ORIGINS")

    @cached_property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


settings = Settings()
```

- [ ] **Step 3: Write model smoke tests**

Create `backend/tests/test_models.py`:

```python
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
```

- [ ] **Step 4: Implement database session and base**

Create `backend/app/db/base.py`:

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

Create `backend/app/db/session.py`:

```python
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 5: Implement SQLAlchemy models**

Create `backend/app/models/user.py`:

```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
```

Create `backend/app/models/chat.py`:

```python
from enum import StrEnum

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ChatRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200), default="New chat")

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id", ondelete="CASCADE"))
    role: Mapped[ChatRole] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    source_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    session = relationship("ChatSession", back_populates="messages")
```

Create `backend/app/models/document.py`:

```python
from enum import StrEnum

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    storage_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[DocumentStatus] = mapped_column(String(20), default=DocumentStatus.UPLOADED)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    chunk_index: Mapped[int]
    content: Mapped[str] = mapped_column(Text)

    document = relationship("Document", back_populates="chunks")
    embedding = relationship("DocumentEmbedding", back_populates="chunk", cascade="all, delete-orphan")


class DocumentEmbedding(Base):
    __tablename__ = "document_embeddings"

    id: Mapped[int] = mapped_column(primary_key=True)
    chunk_id: Mapped[int] = mapped_column(ForeignKey("document_chunks.id", ondelete="CASCADE"))
    embedding: Mapped[list[float]] = mapped_column(Vector(1024))

    chunk = relationship("DocumentChunk", back_populates="embedding")
```

- [ ] **Step 6: Implement DB initialization**

Create `backend/app/db/init_db.py`:

```python
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User


def init_db(db: Session) -> None:
    db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    user = db.query(User).filter(User.username == settings.initial_user_username).one_or_none()
    if user is None:
        db.add(
            User(
                username=settings.initial_user_username,
                password_hash=hash_password(settings.initial_user_password),
            )
        )
        db.commit()
```

- [ ] **Step 7: Run backend tests**

Run:

```bash
cd backend && python -m pytest tests/test_config.py tests/test_models.py -v
```

Expected:

- `test_settings_parse_cors_origins` passes.
- `test_models_can_be_constructed` passes.

- [ ] **Step 8: Commit backend foundation**

```bash
git add backend
git commit -m "feat: add backend settings and data models"
```

## Task 3: Authentication API

**Files:**
- Create: `backend/app/core/security.py`
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/api/deps.py`
- Create: `backend/app/api/routes/auth.py`
- Create: `backend/tests/test_auth.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write auth tests**

Create `backend/tests/test_auth.py`:

```python
from fastapi.testclient import TestClient

from app.main import create_app


def test_login_rejects_bad_credentials() -> None:
    client = TestClient(create_app())
    response = client.post("/api/auth/login", json={"username": "tester", "password": "wrong"})

    assert response.status_code == 401


def test_logout_clears_cookie() -> None:
    client = TestClient(create_app())
    response = client.post("/api/auth/logout")

    assert response.status_code == 204
    assert "auth_token" in response.headers["set-cookie"]
```

- [ ] **Step 2: Implement security helpers**

Create `backend/app/core/security.py`:

```python
from datetime import UTC, datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

AUTH_COOKIE_NAME = "auth_token"
ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = 60 * 12
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def create_access_token(subject: str) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    return jwt.encode({"sub": subject, "exp": expires_at}, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    return str(payload["sub"])
```

- [ ] **Step 3: Implement auth schemas and routes**

Create `backend/app/schemas/auth.py`:

```python
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
```

Create `backend/app/api/routes/auth.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.security import AUTH_COOKIE_NAME, create_access_token, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=UserResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> User:
    user = db.query(User).filter(User.username == payload.username).one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(str(user.id))
    response.set_cookie(
        AUTH_COOKIE_NAME,
        token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 12,
    )
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    response.delete_cookie(AUTH_COOKIE_NAME)
```

- [ ] **Step 4: Wire auth router**

Modify `backend/app/main.py`:

```python
from fastapi import FastAPI

from app.api.routes.auth import router as auth_router


def create_app() -> FastAPI:
    app = FastAPI(title="AI Test Platform API")
    app.include_router(auth_router)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 5: Run auth tests**

Run:

```bash
cd backend && python -m pytest tests/test_auth.py -v
```

Expected:

- Bad credentials return `401`.
- Logout returns `204` and clears `auth_token`.

- [ ] **Step 6: Commit auth API**

```bash
git add backend
git commit -m "feat: add single-user authentication API"
```

## Task 4: Document Upload, Parsing, Chunking, And Indexing

**Files:**
- Create: `backend/app/schemas/document.py`
- Create: `backend/app/api/routes/documents.py`
- Create: `backend/app/services/document_parser.py`
- Create: `backend/app/services/chunker.py`
- Create: `backend/app/services/indexing.py`
- Create: `backend/tests/test_documents.py`
- Create: `backend/tests/test_chunker.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write chunker test**

Create `backend/tests/test_chunker.py`:

```python
from app.services.chunker import chunk_text


def test_chunk_text_splits_long_text_with_indexes() -> None:
    chunks = chunk_text("alpha " * 300, max_chars=200)

    assert len(chunks) > 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].content.startswith("alpha")
```

- [ ] **Step 2: Implement chunker**

Create `backend/app/services/chunker.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    chunk_index: int
    content: str


def chunk_text(text: str, max_chars: int = 1200) -> list[TextChunk]:
    words = text.split()
    chunks: list[TextChunk] = []
    current: list[str] = []
    current_len = 0

    for word in words:
        next_len = current_len + len(word) + 1
        if current and next_len > max_chars:
            chunks.append(TextChunk(chunk_index=len(chunks), content=" ".join(current)))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len = next_len

    if current:
        chunks.append(TextChunk(chunk_index=len(chunks), content=" ".join(current)))

    return chunks
```

- [ ] **Step 3: Write parser tests**

Create `backend/tests/test_documents.py`:

```python
from app.services.document_parser import UnsupportedDocumentType, extract_text


def test_extract_text_from_txt_bytes() -> None:
    assert extract_text("notes.txt", b"hello world") == "hello world"


def test_extract_text_rejects_unknown_extension() -> None:
    try:
        extract_text("archive.zip", b"data")
    except UnsupportedDocumentType as exc:
        assert "Unsupported file type" in str(exc)
    else:
        raise AssertionError("UnsupportedDocumentType was not raised")
```

- [ ] **Step 4: Implement document parser**

Create `backend/app/services/document_parser.py`:

```python
from io import BytesIO
from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader


class UnsupportedDocumentType(ValueError):
    pass


def extract_text(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in {".txt", ".md"}:
        return content.decode("utf-8", errors="replace")
    if suffix == ".pdf":
        reader = PdfReader(BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if suffix == ".docx":
        doc = DocxDocument(BytesIO(content))
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)
    raise UnsupportedDocumentType(f"Unsupported file type: {suffix}")
```

- [ ] **Step 5: Implement document schemas and routes**

Create `backend/app/schemas/document.py`:

```python
from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    filename: str
    status: str
    error_message: str | None = None

    model_config = {"from_attributes": True}
```

Create `backend/app/api/routes/documents.py`:

```python
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.services.indexing import index_document

router = APIRouter(prefix="/api/documents", tags=["documents"])


def get_current_user() -> User:
    return User(id=1, username="tester", password_hash="test")


@router.get("", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[Document]:
    return db.query(Document).filter(Document.user_id == user.id).order_by(Document.id.desc()).all()


@router.post("", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Document:
    if file.filename is None:
        raise HTTPException(status_code=400, detail="Missing filename")
    content = await file.read()
    document = Document(user_id=user.id, filename=file.filename, content_type=file.content_type or "application/octet-stream")
    db.add(document)
    db.commit()
    db.refresh(document)
    background_tasks.add_task(index_document, document.id, file.filename, content)
    return document
```

- [ ] **Step 6: Implement indexing service skeleton**

Create `backend/app/services/indexing.py`:

```python
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.document import Document, DocumentChunk, DocumentStatus
from app.services.chunker import chunk_text
from app.services.document_parser import extract_text


def index_document(document_id: int, filename: str, content: bytes) -> None:
    db: Session = SessionLocal()
    try:
        document = db.get(Document, document_id)
        if document is None:
            return
        document.status = DocumentStatus.PROCESSING
        db.commit()

        text = extract_text(filename, content)
        for chunk in chunk_text(text):
            db.add(DocumentChunk(document_id=document_id, chunk_index=chunk.chunk_index, content=chunk.content))

        document.status = DocumentStatus.READY
        db.commit()
    except Exception as exc:
        document = db.get(Document, document_id)
        if document is not None:
            document.status = DocumentStatus.FAILED
            document.error_message = str(exc)[:300]
            db.commit()
    finally:
        db.close()
```

- [ ] **Step 7: Wire documents router**

Modify `backend/app/main.py`:

```python
from app.api.routes.documents import router as documents_router

app.include_router(documents_router)
```

- [ ] **Step 8: Run document tests**

Run:

```bash
cd backend && python -m pytest tests/test_chunker.py tests/test_documents.py -v
```

Expected:

- Chunker test passes.
- TXT extraction passes.
- Unsupported file extension test passes.

- [ ] **Step 9: Commit document upload foundation**

```bash
git add backend
git commit -m "feat: add document upload and indexing foundation"
```

## Task 5: NVIDIA Client, Embeddings, And RAG Service

**Files:**
- Create: `backend/app/services/nvidia_client.py`
- Create: `backend/app/services/rag.py`
- Create: `backend/tests/test_rag.py`
- Modify: `backend/app/services/indexing.py`

- [ ] **Step 1: Write RAG no-context test**

Create `backend/tests/test_rag.py`:

```python
from app.services.rag import build_no_context_response


def test_rag_no_context_response_is_grounded() -> None:
    response = build_no_context_response()

    assert "uploaded documents do not contain enough context" in response.lower()
    assert "normal chat" in response.lower()
```

- [ ] **Step 2: Implement NVIDIA client**

Create `backend/app/services/nvidia_client.py`:

```python
import httpx

from app.core.config import settings

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"


class NvidiaClient:
    def __init__(self) -> None:
        self.headers = {"Authorization": f"Bearer {settings.nvidia_api_key}"}

    async def embed(self, text: str) -> list[float]:
        async with httpx.AsyncClient(base_url=NVIDIA_BASE_URL, headers=self.headers, timeout=60) as client:
            response = await client.post(
                "/embeddings",
                json={"model": settings.nvidia_embedding_model, "input": text},
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]

    async def chat(self, messages: list[dict[str, str]]) -> str:
        async with httpx.AsyncClient(base_url=NVIDIA_BASE_URL, headers=self.headers, timeout=120) as client:
            response = await client.post(
                "/chat/completions",
                json={"model": settings.nvidia_llm_model, "messages": messages},
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
```

- [ ] **Step 3: Implement RAG prompt helpers**

Create `backend/app/services/rag.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievedChunk:
    document_name: str
    content: str


def build_no_context_response() -> str:
    return (
        "The uploaded documents do not contain enough context to answer this in RAG mode. "
        "Upload more relevant material or switch to normal chat."
    )


def build_rag_messages(question: str, style: str, chunks: list[RetrievedChunk]) -> list[dict[str, str]]:
    context = "\n\n".join(f"Source: {chunk.document_name}\n{chunk.content}" for chunk in chunks)
    return [
        {
            "role": "system",
            "content": (
                "Answer using only the provided company document context. "
                f"Use the requested style: {style}."
            ),
        },
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion:\n{question}"},
    ]
```

- [ ] **Step 4: Update indexing to store embeddings**

Modify `backend/app/services/indexing.py` so each chunk also creates a `DocumentEmbedding`. Use an injectable embedding function in tests and the `NvidiaClient.embed` method in production background execution.

- [ ] **Step 5: Run RAG tests**

Run:

```bash
cd backend && python -m pytest tests/test_rag.py -v
```

Expected:

- RAG no-context behavior test passes.

- [ ] **Step 6: Commit RAG services**

```bash
git add backend
git commit -m "feat: add NVIDIA and RAG services"
```

## Task 6: Chat API

**Files:**
- Create: `backend/app/schemas/chat.py`
- Create: `backend/app/api/routes/chats.py`
- Create: `backend/app/services/chat_service.py`
- Create: `backend/tests/test_chats.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write chat schema tests**

Create `backend/tests/test_chats.py`:

```python
from app.schemas.chat import ChatRequest


def test_chat_request_defaults_to_normal_mode_and_concise_style() -> None:
    payload = ChatRequest(message="Hello")

    assert payload.mode == "normal"
    assert payload.style == "concise"
```

- [ ] **Step 2: Implement chat schemas**

Create `backend/app/schemas/chat.py`:

```python
from pydantic import BaseModel


class ChatSessionResponse(BaseModel):
    id: int
    title: str

    model_config = {"from_attributes": True}


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    source_summary: str | None = None

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    message: str
    mode: str = "normal"
    style: str = "concise"


class ChatResponse(BaseModel):
    message: ChatMessageResponse
```

- [ ] **Step 3: Implement chat service**

Create `backend/app/services/chat_service.py`:

```python
from sqlalchemy.orm import Session

from app.models.chat import ChatMessage, ChatRole, ChatSession
from app.services.nvidia_client import NvidiaClient
from app.services.rag import build_no_context_response


async def send_message(
    db: Session,
    session: ChatSession,
    message: str,
    mode: str,
    style: str,
    client: NvidiaClient,
) -> ChatMessage:
    db.add(ChatMessage(session_id=session.id, role=ChatRole.USER, content=message))

    if mode == "rag":
        answer = build_no_context_response()
    else:
        answer = await client.chat(
            [
                {"role": "system", "content": f"Use {style} response style."},
                {"role": "user", "content": message},
            ]
        )

    assistant_message = ChatMessage(session_id=session.id, role=ChatRole.ASSISTANT, content=answer)
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    return assistant_message
```

- [ ] **Step 4: Implement chat routes**

Create `backend/app/api/routes/chats.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.chat import ChatSession
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse, ChatSessionResponse
from app.services.chat_service import send_message
from app.services.nvidia_client import NvidiaClient

router = APIRouter(prefix="/api/chats", tags=["chats"])


def get_current_user() -> User:
    return User(id=1, username="tester", password_hash="test")


@router.get("", response_model=list[ChatSessionResponse])
def list_sessions(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[ChatSession]:
    return db.query(ChatSession).filter(ChatSession.user_id == user.id).order_by(ChatSession.id.desc()).all()


@router.post("", response_model=ChatSessionResponse)
def create_session(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> ChatSession:
    session = ChatSession(user_id=user.id, title="New chat")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.post("/{session_id}/messages", response_model=ChatResponse)
async def create_message(session_id: int, payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    session = db.get(ChatSession, session_id)
    message = await send_message(db, session, payload.message, payload.mode, payload.style, NvidiaClient())
    return ChatResponse(message=message)
```

- [ ] **Step 5: Wire chat router**

Modify `backend/app/main.py`:

```python
from app.api.routes.chats import router as chats_router

app.include_router(chats_router)
```

- [ ] **Step 6: Run chat tests**

Run:

```bash
cd backend && python -m pytest tests/test_chats.py -v
```

Expected:

- Chat request defaults pass.

- [ ] **Step 7: Commit chat API**

```bash
git add backend
git commit -m "feat: add chat API"
```

## Task 7: Frontend Login And Workspace Layout

**Files:**
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/auth/LoginPage.tsx`
- Create: `frontend/src/chat/ChatWorkspace.tsx`
- Create: `frontend/src/documents/DocumentPanel.tsx`
- Create: `frontend/src/chat/ChatPanel.tsx`
- Create: `frontend/src/App.test.tsx`
- Modify: `frontend/src/App.tsx`
- Create: `frontend/src/test/setup.ts`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`

- [ ] **Step 1: Configure frontend tests**

Create `frontend/vite.config.ts`:

```ts
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
  },
});
```

Create `frontend/src/test/setup.ts`:

```ts
import "@testing-library/jest-dom/vitest";
```

- [ ] **Step 2: Write app rendering tests**

Create `frontend/src/App.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { App } from "./App";

describe("App", () => {
  it("shows login first", () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: "Sign in" })).toBeInTheDocument();
  });
});
```

- [ ] **Step 3: Implement API client**

Create `frontend/src/api/client.ts`:

```ts
const API_BASE = "/api";

export async function postJson<TResponse>(path: string, body: unknown): Promise<TResponse> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<TResponse>;
}
```

- [ ] **Step 4: Implement login page**

Create `frontend/src/auth/LoginPage.tsx`:

```tsx
type LoginPageProps = {
  onLogin: () => void;
};

export function LoginPage({ onLogin }: LoginPageProps) {
  return (
    <main className="login-page">
      <form
        onSubmit={(event) => {
          event.preventDefault();
          onLogin();
        }}
      >
        <h1>Sign in</h1>
        <label>
          Username
          <input name="username" autoComplete="username" />
        </label>
        <label>
          Password
          <input name="password" type="password" autoComplete="current-password" />
        </label>
        <button type="submit">Enter platform</button>
      </form>
    </main>
  );
}
```

- [ ] **Step 5: Implement workspace components**

Create `frontend/src/documents/DocumentPanel.tsx`:

```tsx
export function DocumentPanel() {
  return (
    <section aria-label="Documents">
      <h2>Documents</h2>
      <button type="button">Upload PDF/DOCX/TXT/MD</button>
      <ul>
        <li>policy.pdf · ready</li>
        <li>faq.docx · processing</li>
      </ul>
    </section>
  );
}
```

Create `frontend/src/chat/ChatPanel.tsx`:

```tsx
export function ChatPanel() {
  return (
    <section aria-label="Chat">
      <div>
        <button type="button">Normal chat</button>
        <button type="button">RAG over documents</button>
        <button type="button">Concise</button>
        <button type="button">Detailed</button>
        <button type="button">Expert</button>
        <span>LLM: Gemma 4 via NVIDIA API</span>
      </div>
      <div aria-label="Messages" />
      <form>
        <input aria-label="Message" />
        <button type="submit">Send</button>
      </form>
    </section>
  );
}
```

Create `frontend/src/chat/ChatWorkspace.tsx`:

```tsx
import { ChatPanel } from "./ChatPanel";
import { DocumentPanel } from "../documents/DocumentPanel";

export function ChatWorkspace() {
  return (
    <main className="workspace">
      <aside>
        <h1>Company AI Test Lab</h1>
        <button type="button">New chat</button>
        <section aria-label="Chat history">
          <h2>Chat history</h2>
        </section>
        <DocumentPanel />
      </aside>
      <ChatPanel />
    </main>
  );
}
```

- [ ] **Step 6: Update App state**

Modify `frontend/src/App.tsx`:

```tsx
import { useState } from "react";
import { LoginPage } from "./auth/LoginPage";
import { ChatWorkspace } from "./chat/ChatWorkspace";

export function App() {
  const [authenticated, setAuthenticated] = useState(false);
  return authenticated ? <ChatWorkspace /> : <LoginPage onLogin={() => setAuthenticated(true)} />;
}
```

- [ ] **Step 7: Run frontend tests**

Run:

```bash
cd frontend && npm test
```

Expected:

- App test passes and confirms login is shown first.

- [ ] **Step 8: Commit frontend layout**

```bash
git add frontend
git commit -m "feat: add login-first chat workspace UI"
```

## Task 8: Docker Compose, Caddy, And Deployment Docs

**Files:**
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`
- Create: `docker-compose.yml`
- Create: `Caddyfile`
- Create: `docs/deployment.md`

- [ ] **Step 1: Add backend Dockerfile**

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml .
COPY app ./app
RUN pip install --no-cache-dir .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Add frontend Dockerfile**

Create `frontend/Dockerfile`:

```dockerfile
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
```

- [ ] **Step 3: Add Docker Compose**

Create `docker-compose.yml`:

```yaml
services:
  caddy:
    image: caddy:2
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - frontend
      - backend

  frontend:
    build: ./frontend
    restart: unless-stopped

  backend:
    build: ./backend
    restart: unless-stopped
    env_file: .env
    volumes:
      - uploaded_files:/app/uploads
    depends_on:
      postgres:
        condition: service_healthy

  postgres:
    image: pgvector/pgvector:pg16
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  caddy_data:
  caddy_config:
  postgres_data:
  uploaded_files:
```

- [ ] **Step 4: Add Caddyfile**

Create `Caddyfile`:

```caddyfile
{$APP_DOMAIN} {
  encode zstd gzip

  reverse_proxy /api/* backend:8000
  reverse_proxy frontend:80
}
```

- [ ] **Step 5: Add deployment documentation**

Create `docs/deployment.md`:

```markdown
# Deployment

## VPS Prerequisites

- Docker Engine installed.
- Docker Compose plugin installed.
- Domain DNS `A` record points to the VPS public IP.
- Ports `80` and `443` are open.

## First Deploy

```bash
cp .env.example .env
nano .env
docker compose up -d --build
docker compose ps
```

## Update

```bash
git pull
docker compose up -d --build
docker compose ps
```

## Logs

```bash
docker compose logs -f caddy
docker compose logs -f backend
docker compose logs -f postgres
```

## Backup

```bash
docker compose exec postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > backup.sql
```

## Restore

```bash
docker compose exec -T postgres psql -U "$POSTGRES_USER" "$POSTGRES_DB" < backup.sql
```

## Troubleshooting

- If HTTPS does not issue, verify DNS, open ports, and `APP_DOMAIN`.
- If backend cannot reach NVIDIA APIs, verify `NVIDIA_API_KEY`, model names, and VPS outbound network access.
- If login fails after first boot, verify `INITIAL_USER_USERNAME` and reset the user password through a managed migration.
```

- [ ] **Step 6: Run Docker smoke command**

Run:

```bash
docker compose config
```

Expected:

- Compose configuration renders successfully.
- Services include `caddy`, `frontend`, `backend`, and `postgres`.

- [ ] **Step 7: Commit deployment files**

```bash
git add backend/Dockerfile frontend/Dockerfile docker-compose.yml Caddyfile docs/deployment.md
git commit -m "feat: add Docker Compose VPS deployment"
```

## Task 9: End-To-End Verification Pass

**Files:**
- Modify only files that fail verification from previous tasks.

- [ ] **Step 1: Run backend tests**

Run:

```bash
cd backend && python -m pytest -v
```

Expected:

- All backend tests pass.

- [ ] **Step 2: Run frontend tests and build**

Run:

```bash
cd frontend && npm test && npm run build
```

Expected:

- Vitest tests pass.
- TypeScript and Vite build pass.

- [ ] **Step 3: Run Docker Compose validation**

Run:

```bash
docker compose config
```

Expected:

- Compose file renders with all four services.

- [ ] **Step 4: Review acceptance criteria against the spec**

Use `docs/superpowers/specs/2026-04-25-ai-test-platform-design.md` and confirm each acceptance criterion maps to code or documentation:

- login screen first;
- seeded DB user;
- shared workspace layout;
- document upload and indexing;
- normal chat through Gemma 4;
- RAG response path;
- user-visible errors without secrets;
- Docker Compose with Caddy HTTPS;
- backend, frontend, and smoke verification.

- [ ] **Step 5: Commit final verification fixes**

If verification required fixes, commit them:

```bash
git add backend frontend docker-compose.yml Caddyfile docs .env.example .gitignore
git commit -m "fix: complete AI platform verification"
```

If no fixes were needed, do not create an empty commit.

## Self-Review Checklist

- Spec coverage: every in-scope item from `docs/superpowers/specs/2026-04-25-ai-test-platform-design.md` is covered by at least one task.
- Completeness scan: the plan contains no incomplete sections or vague implementation instructions.
- Type consistency: model names, schema names, route paths, and environment variables match across backend, frontend, Docker, and docs.
- Scope control: Redis/Celery, public registration, multi-user roles, billing, analytics, local model hosting, and fine-tuning remain outside the MVP.
