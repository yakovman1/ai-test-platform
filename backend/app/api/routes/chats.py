from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.chat import ChatSession
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse, ChatSessionResponse
from app.services.chat_service import send_message
from app.services.nvidia_client import NvidiaClient

router = APIRouter(prefix="/api/chats", tags=["chats"])


def get_nvidia_client() -> NvidiaClient:
    return NvidiaClient()


@router.get("", response_model=list[ChatSessionResponse])
def list_chats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ChatSession]:
    return list(
        db.scalars(
            select(ChatSession)
            .where(ChatSession.user_id == current_user.id)
            .order_by(ChatSession.id.desc())
        )
    )


@router.post("", response_model=ChatSessionResponse)
def create_chat(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatSession:
    session = ChatSession(user_id=current_user.id, title="New chat")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.post("/{session_id}/messages", response_model=ChatResponse)
def create_chat_message(
    session_id: int,
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    client: NvidiaClient = Depends(get_nvidia_client),
) -> ChatResponse:
    session = db.scalar(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        )
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    try:
        message = send_message(db, session, payload.message, payload.mode, payload.style, client)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ChatResponse(message=message)
