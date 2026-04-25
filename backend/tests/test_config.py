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
