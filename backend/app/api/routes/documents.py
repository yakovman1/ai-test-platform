from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.services.indexing import index_document

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}
UPLOADS_DIR = Path(__file__).resolve().parents[3] / "uploads"

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Document]:
    return list(
        db.scalars(
            select(Document)
            .where(Document.user_id == current_user.id)
            .order_by(Document.id.desc())
        )
    )


@router.post("", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Document:
    filename = _validate_filename(file.filename)
    content = await file.read()
    _validate_size(content)

    document = Document(
        user_id=current_user.id,
        filename=filename,
        content_type=file.content_type or "application/octet-stream",
    )
    db.add(document)
    db.flush()

    storage_path = _store_upload(document.id, filename, content)
    document.storage_path = str(storage_path)
    db.commit()
    db.refresh(document)

    background_tasks.add_task(index_document, document.id, document.filename, content)
    return document


def _validate_filename(filename: str | None) -> str:
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {suffix}",
        )

    return Path(filename).name


def _validate_size(content: bytes) -> None:
    max_bytes = get_settings().upload_max_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {get_settings().upload_max_mb} MB",
        )


def _store_upload(document_id: int, filename: str, content: bytes) -> Path:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    storage_path = UPLOADS_DIR / f"{document_id}-{uuid4().hex}{Path(filename).suffix.lower()}"
    storage_path.write_bytes(content)
    return storage_path
