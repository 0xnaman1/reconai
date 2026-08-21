"""Backend tools the chat agent is allowed to call.

Every tool takes controlled, typed arguments and returns a JSON-serializable
dict. The agent never receives raw database access: it can only reach the
operations defined here, so the set of things it can do is fixed by this module
rather than by whatever the model decides to ask for.

Each call is recorded in agent_actions with its input and output, giving an
audit trail of what the agent actually did on the user's behalf.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from recon_ai_core.constants import JobStatus, MatchStatus, TransactionSource
from recon_ai_core.models import AgentAction, Match, ReconciliationJob, Transaction
from recon_ai_core.queue import enqueue_reconciliation_job
from recon_ai_core.reporting import (
    build_reconciliation_summary,
    list_unmatched_transactions,
)

# Listing tools cap their output so a large job cannot flood the model's context.
MAX_ROWS = 50


class ToolError(Exception):
    """Raised when a tool cannot complete. The message is shown to the agent."""


def _parse_uuid(value: Any, field: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError) as exc:
        raise ToolError(f"{field} is not a valid id: {value!r}") from exc


def _require_job(session: Session, job_id: uuid.UUID) -> ReconciliationJob:
    job = session.get(ReconciliationJob, job_id)
    if job is None:
        raise ToolError(f"No reconciliation job exists with id {job_id}")
    return job


def _require_match(session: Session, match_id: uuid.UUID) -> Match:
    match = session.get(Match, match_id)
    if match is None:
        raise ToolError(f"No match exists with id {match_id}")
    return match


def _transaction_summary(transaction: Transaction) -> dict[str, Any]:
    return {
        "id": str(transaction.id),
        "source": transaction.source,
        "transaction_date": transaction.transaction_date.isoformat(),
        "description": transaction.description,
        "reference_number": transaction.reference_number,
        "amount": str(transaction.amount),
        "currency": transaction.currency,
    }


def create_reconciliation_job(
    session: Session, bank_pdf_path: str, ledger_pdf_path: str
) -> dict[str, Any]:
    """Queue a reconciliation for two statements already in storage.

    The agent cannot upload files, so the PDFs must have been stored by the
    upload endpoint first; this tool only starts the job that processes them.
    """
    job = ReconciliationJob(
        status=JobStatus.QUEUED.value,
        bank_pdf_path=bank_pdf_path,
        ledger_pdf_path=ledger_pdf_path,
    )
    session.add(job)
    session.flush()

    try:
        enqueue_reconciliation_job(str(job.id))
    except Exception as exc:
        # The row is already flushed and the caller commits regardless, so mark
        # it failed rather than leaving a queued job nothing will ever pick up.
        job.status = JobStatus.FAILED.value
        job.error_message = f"Failed to enqueue reconciliation job: {exc}"
        raise ToolError(f"Could not queue the reconciliation job: {exc}") from exc

    return {"job_id": str(job.id), "status": job.status}


def get_reconciliation_status(session: Session, job_id: str) -> dict[str, Any]:
    """Report where a reconciliation job has reached."""
    job = _require_job(session, _parse_uuid(job_id, "job_id"))
    return {
        "job_id": str(job.id),
        "status": job.status,
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
    }


def get_reconciliation_summary(session: Session, job_id: str) -> dict[str, Any]:
    """Report counts of matched, under-review, reviewed and unmatched rows."""
    job = _require_job(session, _parse_uuid(job_id, "job_id"))
    return build_reconciliation_summary(session, job).model_dump(mode="json")


def list_under_review_matches(session: Session, job_id: str) -> dict[str, Any]:
    """List the matches waiting on a human decision, most confident first."""
    parsed_job_id = _parse_uuid(job_id, "job_id")
    _require_job(session, parsed_job_id)

    matches = session.scalars(
        select(Match)
        .where(
            Match.job_id == parsed_job_id,
            Match.status == MatchStatus.UNDER_REVIEW.value,
        )
        .order_by(Match.confidence_score.desc(), Match.created_at)
        .limit(MAX_ROWS)
    ).all()

    return {
        "job_id": job_id,
        "count": len(matches),
        "matches": [
            {
                "match_id": str(match.id),
                "confidence_score": match.confidence_score,
                "match_type": match.match_type,
                "reason": match.reason,
                "bank_transaction": _transaction_summary(match.bank_transaction),
                "ledger_transaction": _transaction_summary(match.ledger_transaction),
            }
            for match in matches
        ],
    }


def _review_match(
    session: Session, match_id: str, status: MatchStatus
) -> dict[str, Any]:
    match = _require_match(session, _parse_uuid(match_id, "match_id"))
    match.status = status.value
    return {
        "match_id": str(match.id),
        "status": match.status,
        "confidence_score": match.confidence_score,
    }


def approve_match(session: Session, match_id: str) -> dict[str, Any]:
    """Confirm a match pairs the same real transaction."""
    return _review_match(session, match_id, MatchStatus.RECONCILED)


def reject_match(session: Session, match_id: str) -> dict[str, Any]:
    """Record that a match does not pair the same real transaction."""
    return _review_match(session, match_id, MatchStatus.REJECTED)


def list_unmatched(session: Session, job_id: str) -> dict[str, Any]:
    """List transactions with no counterpart, the discrepancies to investigate."""
    parsed_job_id = _parse_uuid(job_id, "job_id")
    _require_job(session, parsed_job_id)

    rows = list_unmatched_transactions(session, parsed_job_id)
    bank = [r for r in rows if r.source == TransactionSource.BANK.value]
    ledger = [r for r in rows if r.source == TransactionSource.LEDGER.value]

    return {
        "job_id": job_id,
        "bank_count": len(bank),
        "ledger_count": len(ledger),
        "bank_transactions": [_transaction_summary(r) for r in bank[:MAX_ROWS]],
        "ledger_transactions": [_transaction_summary(r) for r in ledger[:MAX_ROWS]],
    }


def _tool(name: str, description: str, properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": list(properties),
                "additionalProperties": False,
            },
        },
    }


_JOB_ID = {"type": "string", "description": "Reconciliation job id"}
_MATCH_ID = {"type": "string", "description": "Match id"}

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    _tool(
        "create_reconciliation_job",
        "Start reconciling a bank statement against a ledger. Both PDFs must "
        "already have been uploaded; pass the storage paths returned by the "
        "upload step.",
        {
            "bank_pdf_path": {
                "type": "string",
                "description": "Storage path of the uploaded bank statement PDF",
            },
            "ledger_pdf_path": {
                "type": "string",
                "description": "Storage path of the uploaded ledger PDF",
            },
        },
    ),
    _tool(
        "get_reconciliation_status",
        "Check how far along a reconciliation job is: queued, extracting, "
        "matching, completed, or failed. Reports progress only. For results, "
        "totals, or counts use get_reconciliation_summary instead.",
        {"job_id": _JOB_ID},
    ),
    _tool(
        "get_reconciliation_summary",
        "Get the results of a reconciliation: totals and counts of how many "
        "transactions matched, are awaiting review, were approved or rejected, "
        "and how many stayed unmatched. Use this for any question about how a "
        "reconciliation went or how many of something there are.",
        {"job_id": _JOB_ID},
    ),
    _tool(
        "list_under_review_matches",
        "List matches the engine was not confident enough to accept, which need "
        "the user to approve or reject them.",
        {"job_id": _JOB_ID},
    ),
    _tool(
        "approve_match",
        "Approve a match, confirming both transactions are the same real "
        "transaction. Only call this after the user agrees.",
        {"match_id": _MATCH_ID},
    ),
    _tool(
        "reject_match",
        "Reject a match, recording that the two transactions are not the same "
        "real transaction. Only call this after the user says so.",
        {"match_id": _MATCH_ID},
    ),
    _tool(
        "list_unmatched_transactions",
        "List transactions with no counterpart on the other side. These are the "
        "discrepancies a user needs to investigate.",
        {"job_id": _JOB_ID},
    ),
]

TOOL_IMPLEMENTATIONS: dict[str, Callable[..., dict[str, Any]]] = {
    "create_reconciliation_job": create_reconciliation_job,
    "get_reconciliation_status": get_reconciliation_status,
    "get_reconciliation_summary": get_reconciliation_summary,
    "list_under_review_matches": list_under_review_matches,
    "approve_match": approve_match,
    "reject_match": reject_match,
    "list_unmatched_transactions": list_unmatched,
}


def _log_action(
    session: Session,
    chat_session_id: uuid.UUID | None,
    tool_name: str,
    arguments: dict[str, Any],
    output: dict[str, Any],
) -> None:
    # A rejected call still gets logged, so the job link is only set when the id
    # both parses and exists. Whatever the agent actually sent is preserved in
    # tool_input either way.
    raw_job_id = arguments.get("job_id") or output.get("job_id")
    job_id = None
    if raw_job_id:
        try:
            parsed = uuid.UUID(str(raw_job_id))
        except ValueError, TypeError:
            parsed = None
        if parsed is not None and session.get(ReconciliationJob, parsed) is not None:
            job_id = parsed

    session.add(
        AgentAction(
            session_id=chat_session_id,
            job_id=job_id,
            tool_name=tool_name,
            tool_input=arguments,
            tool_output=output,
        )
    )


def execute_tool(
    session: Session,
    tool_name: str,
    arguments: dict[str, Any],
    chat_session_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    """Run one agent tool call and record it in agent_actions.

    A tool that fails returns an error dict rather than raising, so the agent can
    explain the problem to the user instead of the conversation breaking. The
    call is logged either way, and the tool's effect commits together with its
    log entry so the audit trail cannot drift from what actually happened.
    """
    implementation = TOOL_IMPLEMENTATIONS.get(tool_name)
    if implementation is None:
        # Logged like any other call: an attempt to reach a tool that does not
        # exist is worth seeing in the audit trail.
        output = {"error": f"Unknown tool: {tool_name}"}
    else:
        try:
            output = implementation(session, **arguments)
        except ToolError as exc:
            output = {"error": str(exc)}
        except TypeError as exc:
            output = {"error": f"Wrong arguments for {tool_name}: {exc}"}

    _log_action(session, chat_session_id, tool_name, arguments, output)
    session.commit()
    return output
