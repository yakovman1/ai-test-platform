from __future__ import annotations

from sqlalchemy import delete

from app.db.session import SessionLocal
from app.models.document import Document, DocumentChunk, DocumentStatus
from app.services.chunker import chunk_text
from app.services.document_parser import extract_text

MAX_ERROR_MESSAGE_LENGTH = 200


def index_document(document_id: int, filename: str, content: bytes) -> None:
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

        db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
        db.add_all(
            DocumentChunk(
                document_id=document_id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                source_locator=chunk.source_locator,
            )
            for chunk in chunks
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
