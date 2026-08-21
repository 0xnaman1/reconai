from __future__ import annotations

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from recon_ai_core.models import ChatMessage, ChatSession, ReconciliationJob
from recon_ai_core.schemas import (
    ChatMessageCreateRequest,
    ChatMessageResponse,
    ChatSessionCreateRequest,
    ChatSessionResponse,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from recon_ai_api.dependencies import get_db_session
from recon_ai_api.errors import AppError

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


def _load_session(session: Session, session_id: uuid.UUID) -> ChatSession:
    chat_session = session.get(ChatSession, session_id)
    if chat_session is None:
        raise AppError("Chat session not found", status_code=404)
    return chat_session


@router.post("/sessions", response_model=ChatSessionResponse)
def create_chat_session(
    payload: ChatSessionCreateRequest,
    session: Annotated[Session, Depends(get_db_session)],
) -> ChatSessionResponse:
    """Start a chat session, optionally bound to a reconciliation job.

    The job can be left unset when the conversation starts before any upload;
    the agent attaches one once a reconciliation exists.
    """
    if (
        payload.active_job_id is not None
        and session.get(ReconciliationJob, payload.active_job_id) is None
    ):
        raise AppError("Reconciliation job not found", status_code=404)

    chat_session = ChatSession(active_job_id=payload.active_job_id)
    session.add(chat_session)
    session.commit()
    session.refresh(chat_session)

    return ChatSessionResponse.model_validate(chat_session)


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
def get_chat_session(
    session_id: uuid.UUID,
    session: Annotated[Session, Depends(get_db_session)],
) -> ChatSessionResponse:
    """Read a session, including the reconciliation job it is working on."""
    return ChatSessionResponse.model_validate(_load_session(session, session_id))


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
def list_chat_messages(
    session_id: uuid.UUID,
    session: Annotated[Session, Depends(get_db_session)],
) -> list[ChatMessageResponse]:
    """Return the session's messages in the order they were written."""
    _load_session(session, session_id)

    messages = session.scalars(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at, ChatMessage.id)
    ).all()

    return [ChatMessageResponse.model_validate(row) for row in messages]


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
def create_chat_message(
    session_id: uuid.UUID,
    payload: ChatMessageCreateRequest,
    session: Annotated[Session, Depends(get_db_session)],
) -> ChatMessageResponse:
    """Append one message to a session.

    This only persists the message. Generating an assistant reply belongs to the
    agent, so a user message stored here does not produce an answer yet.
    """
    _load_session(session, session_id)

    message = ChatMessage(
        session_id=session_id,
        role=payload.role.value,
        content=payload.content,
        extra_data=payload.metadata,
    )
    session.add(message)
    session.commit()
    session.refresh(message)

    return ChatMessageResponse.model_validate(message)
