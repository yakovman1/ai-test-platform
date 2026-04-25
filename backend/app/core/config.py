from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

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

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
