"""The chat agent: an OpenAI tool-calling loop over the backend tools.

The agent decides what to say and which tools to call. It never touches the
database directly; every effect goes through agent_tools.execute_tool, so the
set of things a conversation can do is bounded by that module.

Each turn is persisted as it happens, including the assistant's tool calls and
their results, so the stored conversation is a complete record that can be
replayed to the model on the next turn.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any, cast

from openai import OpenAIError
from openai.types.chat import (
    ChatCompletionMessage,
    ChatCompletionMessageFunctionToolCall,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from recon_ai_core.agent_tools import TOOL_DEFINITIONS, execute_tool
from recon_ai_core.constants import ChatRole
from recon_ai_core.models import ChatMessage, ChatSession, ReconciliationJob
from recon_ai_core.openai_client import get_openai_client
from recon_ai_core.settings import get_settings

logger = logging.getLogger(__name__)

# A turn that keeps calling tools without answering is stuck; stop and say so
# rather than looping against the API.
MAX_TOOL_ROUNDS = 5


class AgentError(Exception):
    """Raised when a turn cannot be completed."""


SYSTEM_PROMPT = """\
You are the assistant for Recon AI, a reconciliation tool that matches bank \
statement transactions against general ledger transactions.

You answer using the tools provided. Never guess at numbers, statuses, or \
match details: call a tool and report what it returns. If a tool returns an \
error, tell the user plainly what went wrong.

How reconciliation works here, so you can explain it:

- Every transaction is normalized to one signed amount. Money out is negative.
- The matching engine scores each candidate pair out of 100: exact amount is \
worth 40, exact date 25 (less as the dates drift apart), exact reference 25, \
and description similarity up to 10.
- Scoring 90 or above is matched automatically. 70 to 89 is held for review \
because the evidence was incomplete, usually a missing reference or dates a \
few days apart. Below 70 the transactions are left unmatched.
- An unmatched transaction is not a failure of the tool. It usually means a \
real discrepancy: a fee, a wrong amount, or an entry missing from one side. \
These are what the user most needs to look at.
- Unmatched does not mean unreconcilable. list_match_suggestions ranks the \
closest remaining candidates for each unmatched transaction, and the user can \
pair one with manual_match. A low score is often a real difference worth \
naming, such as a bank fee, so say what differs rather than only the number.

When presenting a match that needs review, show both sides so the user can \
judge it, and give the confidence and the reason:

  Bank:   3 Aug 2026, AWS PAYMENT, ref TXN123, -250.00
  Ledger: 4 Aug 2026, Amazon Web Services invoice, -250.00
  Confidence 82. Amount matched exactly, dates differ by 1 day.

Then ask whether to approve or reject it.

Only call approve_match, reject_match or manual_match after the user has \
clearly said which one they want, for a specific match or pair. Never decide on \
your own initiative, and never guess an id: read it from a tool result. If the \
user says something ambiguous like "yes", make sure it is clear which one they \
mean before acting.

Be concise. Prefer plain sentences and short lists over tables. Amounts and \
dates should read the way a person would write them.\
"""


def _function_tool_calls(
    message: ChatCompletionMessage,
) -> list[ChatCompletionMessageFunctionToolCall]:
    """The function calls in a reply.

    Only function tools are registered, so any other kind of call the SDK models
    is not something this agent asked for and is ignored.
    """
    return [
        call
        for call in (message.tool_calls or [])
        if isinstance(call, ChatCompletionMessageFunctionToolCall)
    ]


def _tool_calls_payload(
    calls: list[ChatCompletionMessageFunctionToolCall],
) -> list[dict[str, Any]]:
    return [
        {
            "id": call.id,
            "type": "function",
            "function": {
                "name": call.function.name,
                "arguments": call.function.arguments,
            },
        }
        for call in calls
    ]


def _to_openai_message(row: ChatMessage) -> ChatCompletionMessageParam:
    """Rebuild the OpenAI message that produced or followed from a stored row.

    The shape is built from stored data rather than literals, so it is cast to
    the SDK's union rather than matching one of its members statically.
    """
    if row.role == ChatRole.TOOL.value:
        return cast(
            ChatCompletionMessageParam,
            {
                "role": "tool",
                "tool_call_id": row.extra_data.get("tool_call_id", ""),
                "content": row.content,
            },
        )

    message: dict[str, Any] = {"role": row.role, "content": row.content}
    tool_calls = row.extra_data.get("tool_calls")
    if tool_calls:
        # OpenAI rejects an empty string here when tool calls are present.
        message["content"] = row.content or None
        message["tool_calls"] = tool_calls
    return cast(ChatCompletionMessageParam, message)


def _load_history(session: Session, chat_session_id: uuid.UUID) -> list[ChatMessage]:
    return list(
        session.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == chat_session_id)
            .order_by(ChatMessage.created_at, ChatMessage.id)
        ).all()
    )


def _append(
    session: Session,
    chat_session_id: uuid.UUID,
    role: ChatRole,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> ChatMessage:
    message = ChatMessage(
        session_id=chat_session_id,
        role=role.value,
        content=content,
        extra_data=metadata or {},
    )
    session.add(message)
    session.commit()
    return message


def _system_message(chat_session: ChatSession) -> ChatCompletionMessageParam:
    """The system prompt, plus which job the conversation is currently about."""
    content = SYSTEM_PROMPT
    if chat_session.active_job_id is not None:
        content += (
            f"\n\nThe user is currently working on reconciliation job "
            f"{chat_session.active_job_id}. Use this job id when they do not "
            f"name one."
        )
    return {"role": "system", "content": content}


def _remember_active_job(
    session: Session, chat_session: ChatSession, output: dict[str, Any]
) -> None:
    """Point the session at whichever job a tool just acted on."""
    raw = output.get("job_id")
    if not raw:
        return
    try:
        job_id = uuid.UUID(str(raw))
    except (ValueError, TypeError):
        return
    if job_id != chat_session.active_job_id and session.get(ReconciliationJob, job_id):
        chat_session.active_job_id = job_id


def run_agent_turn(
    session: Session, chat_session_id: uuid.UUID, user_message: str
) -> list[ChatMessage]:
    """Run one user turn to completion and return every message it appended.

    The user message is stored first so it survives even if the model call
    fails, then the loop runs until the model answers without asking for more
    tools.
    """
    chat_session = session.get(ChatSession, chat_session_id)
    if chat_session is None:
        raise AgentError(f"Chat session {chat_session_id} not found")

    appended = [_append(session, chat_session_id, ChatRole.USER, user_message)]

    client = get_openai_client()
    model = get_settings().openai_chat_model

    for _ in range(MAX_TOOL_ROUNDS):
        history = _load_history(session, chat_session_id)
        messages: list[ChatCompletionMessageParam] = [
            _system_message(chat_session),
            *(_to_openai_message(row) for row in history),
        ]

        try:
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=cast(list[ChatCompletionToolParam], TOOL_DEFINITIONS),
                tool_choice="auto",
            )
        except OpenAIError as exc:
            raise AgentError(f"The assistant could not respond: {exc}") from exc

        reply = completion.choices[0].message
        tool_calls = _function_tool_calls(reply)

        if not tool_calls:
            appended.append(
                _append(
                    session,
                    chat_session_id,
                    ChatRole.ASSISTANT,
                    reply.content or "",
                )
            )
            return appended

        appended.append(
            _append(
                session,
                chat_session_id,
                ChatRole.ASSISTANT,
                reply.content or "",
                {"tool_calls": _tool_calls_payload(tool_calls)},
            )
        )

        for call in tool_calls:
            try:
                arguments = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                arguments = {}

            output = execute_tool(
                session, call.function.name, arguments, chat_session_id
            )
            _remember_active_job(session, chat_session, output)

            appended.append(
                _append(
                    session,
                    chat_session_id,
                    ChatRole.TOOL,
                    json.dumps(output, default=str),
                    {"tool_call_id": call.id, "tool_name": call.function.name},
                )
            )

    logger.warning(
        "Agent hit the tool round limit for chat session %s", chat_session_id
    )
    appended.append(
        _append(
            session,
            chat_session_id,
            ChatRole.ASSISTANT,
            "I wasn't able to finish that. Could you try asking a different way?",
        )
    )
    return appended
