from __future__ import annotations

import uuid

from sqlalchemy import delete
from sqlalchemy.orm import Session

from recon_ai_core.constants import TransactionSource
from recon_ai_core.models import Match, Transaction
from recon_ai_core.schemas import ExtractedTransaction


def _build_transaction(
    job_id: uuid.UUID, source: TransactionSource, extracted: ExtractedTransaction
) -> Transaction:
    return Transaction(
        job_id=job_id,
        source=source.value,
        transaction_date=extracted.transaction_date,
        description=extracted.description,
        reference_number=extracted.reference_number,
        amount=extracted.amount,
        currency=extracted.currency,
        raw_text=extracted.raw_text,
        extra_data=extracted.metadata,
    )


def replace_job_transactions(
    session: Session,
    job_id: uuid.UUID,
    bank_transactions: list[ExtractedTransaction],
    ledger_transactions: list[ExtractedTransaction],
) -> dict[str, int]:
    """Replace every transaction stored for a job.

    Matches are removed first because they reference transactions. Clearing both
    keeps a re-run of the same job from stacking duplicate rows on top of an
    earlier attempt.
    """
    session.execute(delete(Match).where(Match.job_id == job_id))
    session.execute(delete(Transaction).where(Transaction.job_id == job_id))

    session.add_all(
        [
            _build_transaction(job_id, TransactionSource.BANK, extracted)
            for extracted in bank_transactions
        ]
        + [
            _build_transaction(job_id, TransactionSource.LEDGER, extracted)
            for extracted in ledger_transactions
        ]
    )

    return {
        TransactionSource.BANK.value: len(bank_transactions),
        TransactionSource.LEDGER.value: len(ledger_transactions),
    }
