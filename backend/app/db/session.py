from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


SessionLocal = sessionmaker(autocommit=False, autoflush=False)

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine

    if _engine is None:
        _engine = create_engine(get_settings().database_url, pool_pre_ping=True)
        SessionLocal.configure(bind=_engine)

    return _engine


def get_db() -> Generator[Session]:
    get_engine()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
