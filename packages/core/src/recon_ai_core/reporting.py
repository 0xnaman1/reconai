from __future__ import annotations

import uuid

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from recon_ai_core.constants import JobStatus, MatchStatus, TransactionSource
from recon_ai_core.models import Match, ReconciliationJob, Transaction
from recon_ai_core.schemas import ReconciliationSummaryResponse

# A rejected match no longer claims its transactions, so both sides return to
# the unmatched pool.
ACTIVE_MATCH_STATUSES = [
    MatchStatus.MATCHED.value,
    MatchStatus.UNDER_REVIEW.value,
    MatchStatus.RECONCILED.value,
]


def _count_transactions(
    session: Session, job_id: uuid.UUID, source: TransactionSource
) -> int:
    return (
        session.scalar(
            select(func.count(Transaction.id)).where(
                Transaction.job_id == job_id,
                Transaction.source == source.value,
            )
        )
        or 0
    )


def _count_matches(session: Session, job_id: uuid.UUID, status: MatchStatus) -> int:
    return (
        session.scalar(
            select(func.count(Match.id)).where(
                Match.job_id == job_id,
                Match.status == status.value,
            )
        )
        or 0
    )


def build_reconciliation_summary(
    session: Session, job: ReconciliationJob
) -> ReconciliationSummaryResponse:
    """Summarize a job's transactions and matches.

    Unmatched counts are derived rather than stored: an unmatched transaction is
    simply one that no active match points at.
    """
    bank_count = _count_transactions(session, job.id, TransactionSource.BANK)
    ledger_count = _count_transactions(session, job.id, TransactionSource.LEDGER)

    matched_bank_count = (
        session.scalar(
            select(func.count(distinct(Match.bank_transaction_id))).where(
                Match.job_id == job.id,
                Match.status.in_(ACTIVE_MATCH_STATUSES),
            )
        )
        or 0
    )
    matched_ledger_count = (
        session.scalar(
            select(func.count(distinct(Match.ledger_transaction_id))).where(
                Match.job_id == job.id,
                Match.status.in_(ACTIVE_MATCH_STATUSES),
            )
        )
        or 0
    )

    return ReconciliationSummaryResponse(
        job_id=job.id,
        status=JobStatus(job.status),
        bank_transaction_count=bank_count,
        ledger_transaction_count=ledger_count,
        matched_count=_count_matches(session, job.id, MatchStatus.MATCHED),
        under_review_count=_count_matches(session, job.id, MatchStatus.UNDER_REVIEW),
        reconciled_count=_count_matches(session, job.id, MatchStatus.RECONCILED),
        rejected_count=_count_matches(session, job.id, MatchStatus.REJECTED),
        unmatched_bank_count=max(bank_count - matched_bank_count, 0),
        unmatched_ledger_count=max(ledger_count - matched_ledger_count, 0),
    )


def list_unmatched_transactions(
    session: Session, job_id: uuid.UUID
) -> list[Transaction]:
    """Return a job's transactions that no active match points at."""
    claimed_bank = select(Match.bank_transaction_id).where(
        Match.job_id == job_id, Match.status.in_(ACTIVE_MATCH_STATUSES)
    )
    claimed_ledger = select(Match.ledger_transaction_id).where(
        Match.job_id == job_id, Match.status.in_(ACTIVE_MATCH_STATUSES)
    )

    return list(
        session.scalars(
            select(Transaction)
            .where(
                Transaction.job_id == job_id,
                Transaction.id.notin_(claimed_bank.union(claimed_ledger)),
            )
            .order_by(Transaction.source, Transaction.transaction_date, Transaction.id)
        ).all()
    )
