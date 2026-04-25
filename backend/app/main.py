from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.api.routes.auth import router as auth_router
from app.api.routes.documents import router as documents_router
from app.core.config import get_settings
from app.db.init_db import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="AI Test Platform API", lifespan=lifespan)
    _add_cors_middleware(app)
    app.include_router(auth_router)
    app.include_router(documents_router)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


def _add_cors_middleware(app: FastAPI) -> None:
    try:
        origins = get_settings().cors_origins
    except ValidationError:
        origins = []

    if not origins:
        return

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )


app = create_app()
