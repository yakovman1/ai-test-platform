from __future__ import annotations

from math import sqrt
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.chat import ChatMessage, ChatRole, ChatSession
from app.models.document import Document, DocumentChunk, DocumentEmbedding, DocumentStatus
from app.services.rag import RetrievedChunk, build_no_context_response, build_rag_messages

SUPPORTED_MODES = {"normal", "rag"}
SUPPORTED_STYLES = {"concise", "detailed", "expert"}


class ChatClient(Protocol):
    def embed(self, text: str) -> list[float]: ...
    def chat(self, messages: list[dict[str, str]]) -> str: ...


class ChatGenerationError(Exception):
    pass


def send_message(
    db: Session,
    session: ChatSession,
    message: str,
    mode: str,
    style: str,
    client: ChatClient,
) -> ChatMessage:
    _validate_mode(mode)
    _validate_style(style)

    user_message = ChatMessage(session=session, role=ChatRole.USER, content=message)
    db.add(user_message)
    db.commit()

    try:
        if mode == "rag":
            chunks = _retrieve_chunks(db, session.user_id, client.embed(message))
            assistant_content = _build_rag_response(message, style, chunks, client)
            source_summary = _source_summary(chunks)
        else:
            assistant_content = client.chat(_build_normal_messages(message, style))
            source_summary = None
    except Exception as exc:
        db.rollback()
        raise ChatGenerationError("Chat response failed") from exc

    assistant_message = ChatMessage(
        session=session,
        role=ChatRole.ASSISTANT,
        content=assistant_content,
        source_summary=source_summary,
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    return assistant_message


def _build_normal_messages(message: str, style: str) -> list[dict[str, str]]:
    article = "an" if style == "expert" else "a"
    return [
        {
            "role": "system",
            "content": f"Respond in {article} {style} style for an internal company assistant.",
        },
        {"role": "user", "content": message},
    ]


def _build_rag_response(
    message: str,
    style: str,
    chunks: list[RetrievedChunk],
    client: ChatClient,
) -> str:
    if not chunks:
        return build_no_context_response()

    return client.chat(build_rag_messages(message, style, chunks))


def _retrieve_chunks(
    db: Session,
    user_id: int,
    question_embedding: list[float],
) -> list[RetrievedChunk]:
    top_k = get_settings().rag_top_k
    if top_k <= 0:
        return []

    distance = DocumentEmbedding.embedding.cosine_distance(question_embedding)
    stmt = (
        select(Document.filename, DocumentChunk.content)
        .join(DocumentChunk, DocumentChunk.document_id == Document.id)
        .join(DocumentEmbedding, DocumentEmbedding.chunk_id == DocumentChunk.id)
        .where(Document.user_id == user_id, Document.status == DocumentStatus.READY)
        .order_by(distance)
        .limit(top_k)
    )
    try:
        rows = db.execute(stmt).all()
    except SQLAlchemyError:
        rows = _retrieve_chunks_in_python(db, user_id, question_embedding, top_k)

    return [RetrievedChunk(document_name=filename, content=content) for filename, content in rows]


def _retrieve_chunks_in_python(
    db: Session,
    user_id: int,
    question_embedding: list[float],
    top_k: int,
) -> list[tuple[str, str]]:
    stmt = (
        select(Document.filename, DocumentChunk.content, DocumentEmbedding.embedding)
        .join(DocumentChunk, DocumentChunk.document_id == Document.id)
        .join(DocumentEmbedding, DocumentEmbedding.chunk_id == DocumentChunk.id)
        .where(Document.user_id == user_id, Document.status == DocumentStatus.READY)
    )
    rows = db.execute(stmt).all()
    ranked_rows = sorted(
        rows,
        key=lambda row: _cosine_distance(question_embedding, row.embedding),
    )
    return [(row.filename, row.content) for row in ranked_rows[:top_k]]


def _cosine_distance(left: list[float], right: list[float]) -> float:
    dot_product = sum(a * b for a, b in zip(left, right, strict=False))
    left_norm = sqrt(sum(value * value for value in left))
    right_norm = sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 1.0
    return 1 - dot_product / (left_norm * right_norm)


def _source_summary(chunks: list[RetrievedChunk]) -> str | None:
    if not chunks:
        return None

    document_names = sorted({chunk.document_name for chunk in chunks})
    return ", ".join(document_names)


def _validate_mode(mode: str) -> None:
    if mode not in SUPPORTED_MODES:
        raise ValueError(f"Unsupported chat mode: {mode}")


def _validate_style(style: str) -> None:
    if style not in SUPPORTED_STYLES:
        raise ValueError(f"Unsupported chat style: {style}")
