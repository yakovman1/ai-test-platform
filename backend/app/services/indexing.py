from __future__ import annotations

from collections.abc import Callable

from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.models.document import Document, DocumentChunk, DocumentEmbedding, DocumentStatus
from app.services.chunker import chunk_text
from app.services.document_parser import extract_text
from app.services.nvidia_client import NvidiaClient

MAX_ERROR_MESSAGE_LENGTH = 200


def index_document(
    document_id: int,
    filename: str,
    content: bytes,
    embedding_provider: Callable[[str], list[float]] | None = None,
) -> None:
    db = SessionLocal()
    try:
        document = db.get(Document, document_id)
        if document is None:
            return

        document.status = DocumentStatus.PROCESSING
        document.error_message = None
        db.commit()

        text = extract_text(filename, content)
        chunks = chunk_text(text)
        embed_text = embedding_provider or _default_embedding_provider

        chunk_ids = select(DocumentChunk.id).where(DocumentChunk.document_id == document_id)
        db.execute(delete(DocumentEmbedding).where(DocumentEmbedding.chunk_id.in_(chunk_ids)))
        db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
        document_chunks = [
            DocumentChunk(
                document_id=document_id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                source_locator=chunk.source_locator,
            )
            for chunk in chunks
        ]
        db.add_all(document_chunks)
        db.flush()
        db.add_all(
            DocumentEmbedding(chunk_id=chunk.id, embedding=embed_text(chunk.content))
            for chunk in document_chunks
        )
        document.status = DocumentStatus.READY
        document.error_message = None
        db.commit()
    except Exception as exc:
        db.rollback()
        failed_document = db.get(Document, document_id)
        if failed_document is not None:
            failed_document.status = DocumentStatus.FAILED
            failed_document.error_message = _safe_error_message(exc)
            db.commit()
    finally:
        db.close()


def _safe_error_message(exc: Exception) -> str:
    message = str(exc) or exc.__class__.__name__
    return message[:MAX_ERROR_MESSAGE_LENGTH]


def _default_embedding_provider(text: str) -> list[float]:
    return NvidiaClient().embed(text)
