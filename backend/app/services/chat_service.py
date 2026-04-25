from __future__ import annotations

from typing import Protocol

from sqlalchemy.orm import Session

from app.models.chat import ChatMessage, ChatRole, ChatSession
from app.services.rag import RetrievedChunk, build_no_context_response, build_rag_messages

SUPPORTED_MODES = {"normal", "rag"}
SUPPORTED_STYLES = {"concise", "detailed"}


class ChatClient(Protocol):
    def chat(self, messages: list[dict[str, str]]) -> str: ...


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

    chunks = _retrieve_chunks()
    if mode == "rag":
        assistant_content = _build_rag_response(message, style, chunks, client)
        source_summary = _source_summary(chunks)
    else:
        assistant_content = client.chat(_build_normal_messages(message, style))
        source_summary = None

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
    return [
        {
            "role": "system",
            "content": f"Respond in a {style} style for an internal company assistant.",
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


def _retrieve_chunks() -> list[RetrievedChunk]:
    return []


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
