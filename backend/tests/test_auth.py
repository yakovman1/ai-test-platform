from collections.abc import Generator

import bcrypt
import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.security import AUTH_COOKIE_NAME, create_access_token
from app.db.session import get_db
from app import main as main_module
from app.main import create_app
from app.models import chat as _chat  # noqa: F401
from app.models import document as _document  # noqa: F401
from app.models.user import User


@pytest.fixture
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
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_login_rejects_bad_credentials() -> None:
    client = _client_with_user(password="correct-password")

    response = client.post(
        "/api/auth/login",
        json={"username": "tester", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


def test_login_sets_auth_cookie(configured_settings: None) -> None:
    client = _client_with_user(password="correct-password")

    response = client.post(
        "/api/auth/login",
        json={"username": "tester", "password": "correct-password"},
    )

    assert response.status_code == 200
    assert response.json() == {"id": 1, "username": "tester"}
    assert "auth_token=" in response.headers["set-cookie"]
    assert "HttpOnly" in response.headers["set-cookie"]


def test_login_cookie_secure_flag_can_be_disabled_for_local_http(
    configured_settings: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    get_settings.cache_clear()
    client = _client_with_user(password="correct-password")

    response = client.post(
        "/api/auth/login",
        json={"username": "tester", "password": "correct-password"},
    )

    assert response.status_code == 200
    assert "Secure" not in response.headers["set-cookie"]


def test_logout_clears_cookie() -> None:
    client = TestClient(create_app())

    response = client.post("/api/auth/logout")

    assert response.status_code == 204
    assert "auth_token=" in response.headers["set-cookie"]
    assert "Max-Age=0" in response.headers["set-cookie"]


def test_current_user_dependency_rejects_missing_cookie(configured_settings: None) -> None:
    client = _client_with_user(password="correct-password", include_protected_route=True)

    response = client.get("/protected")

    assert response.status_code == 401


def test_current_user_dependency_rejects_invalid_cookie(configured_settings: None) -> None:
    client = _client_with_user(password="correct-password", include_protected_route=True)

    response = client.get("/protected", headers={"cookie": f"{AUTH_COOKIE_NAME}=not-a-token"})

    assert response.status_code == 401


def test_current_user_dependency_resolves_cookie(configured_settings: None) -> None:
    client = _client_with_user(password="correct-password", include_protected_route=True)
    token = create_access_token("1")

    response = client.get("/protected", headers={"cookie": f"{AUTH_COOKIE_NAME}={token}"})

    assert response.status_code == 200
    assert response.json() == {"username": "tester"}


def test_app_startup_initializes_database(
    configured_settings: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    init_calls: list[str] = []

    def fake_init_db() -> None:
        init_calls.append("called")

    monkeypatch.setattr(main_module, "init_db", fake_init_db, raising=False)

    with TestClient(create_app()):
        pass

    assert init_calls == ["called"]


def test_cors_allows_configured_cookie_origins(
    configured_settings: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BACKEND_CORS_ORIGINS", "http://localhost:5173")
    get_settings.cache_clear()
    monkeypatch.setattr(main_module, "init_db", lambda: None, raising=False)

    with TestClient(create_app()) as client:
        response = client.options(
            "/api/auth/login",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.headers["access-control-allow-credentials"] == "true"


def _client_with_user(*, password: str, include_protected_route: bool = False) -> TestClient:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    User.__table__.create(bind=engine)

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    with testing_session_local() as db:
        db.add(User(username="tester", password_hash=password_hash))
        db.commit()

    app = create_app()

    if include_protected_route:

        @app.get("/protected")
        def protected(user: User = Depends(get_current_user)) -> dict[str, str]:
            return {"username": user.username}

    def override_get_db() -> Generator[Session]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)
