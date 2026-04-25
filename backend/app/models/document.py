from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    filename: Mapped[str]
    content_type: Mapped[str]
    storage_path: Mapped[str | None] = mapped_column(nullable=True)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(
            DocumentStatus,
            values_callable=lambda enum_cls: [status.value for status in enum_cls],
        ),
        default=DocumentStatus.UPLOADED,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(nullable=True)

    user: Mapped[User] = relationship(back_populates="documents")
    chunks: Mapped[list[DocumentChunk]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("status", DocumentStatus.UPLOADED)
        super().__init__(**kwargs)


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    chunk_index: Mapped[int]
    content: Mapped[str]

    document: Mapped[Document] = relationship(back_populates="chunks")
    embedding: Mapped[DocumentEmbedding] = relationship(
        back_populates="chunk",
        cascade="all, delete-orphan",
        uselist=False,
    )


class DocumentEmbedding(Base):
    __tablename__ = "document_embeddings"

    id: Mapped[int] = mapped_column(primary_key=True)
    chunk_id: Mapped[int] = mapped_column(ForeignKey("document_chunks.id"))
    embedding: Mapped[list[float]] = mapped_column(Vector(1024))

    chunk: Mapped[DocumentChunk] = relationship(back_populates="embedding")
