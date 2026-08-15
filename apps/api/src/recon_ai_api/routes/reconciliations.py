from __future__ import annotations

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from recon_ai_core.constants import JobStatus, MatchStatus, TransactionSource
from recon_ai_core.models import Match, ReconciliationJob, Transaction
from recon_ai_core.queue import enqueue_reconciliation_job
from recon_ai_core.schemas import (
    ReconciliationCreateResponse,
    ReconciliationDetailResponse,
    ReconciliationJobResponse,
    ReconciliationSummaryResponse,
)
from recon_ai_core.storage import upload_statement_pdf_if_missing
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from recon_ai_api.dependencies import get_db_session
from recon_ai_api.errors import AppError

router = APIRouter(prefix="/reconciliations", tags=["reconciliations"])
logger = logging.getLogger(__name__)


def build_reconciliation_summary(
    session: Session, job: ReconciliationJob
) -> ReconciliationSummaryResponse:
    bank_count = (
        session.scalar(
            select(func.count(Transaction.id)).where(
                Transaction.job_id == job.id,
                Transaction.source == TransactionSource.BANK.value,
            )
        )
        or 0
    )
    ledger_count = (
        session.scalar(
            select(func.count(Transaction.id)).where(
                Transaction.job_id == job.id,
                Transaction.source == TransactionSource.LEDGER.value,
            )
        )
        or 0
    )

    matched_count = (
        session.scalar(
            select(func.count(Match.id)).where(
                Match.job_id == job.id,
                Match.status == MatchStatus.MATCHED.value,
            )
        )
        or 0
    )
    under_review_count = (
        session.scalar(
            select(func.count(Match.id)).where(
                Match.job_id == job.id,
                Match.status == MatchStatus.UNDER_REVIEW.value,
            )
        )
        or 0
    )
    reconciled_count = (
        session.scalar(
            select(func.count(Match.id)).where(
                Match.job_id == job.id,
                Match.status == MatchStatus.RECONCILED.value,
            )
        )
        or 0
    )
    rejected_count = (
        session.scalar(
            select(func.count(Match.id)).where(
                Match.job_id == job.id,
                Match.status == MatchStatus.REJECTED.value,
            )
        )
        or 0
    )

    active_statuses = [
        MatchStatus.MATCHED.value,
        MatchStatus.UNDER_REVIEW.value,
        MatchStatus.RECONCILED.value,
    ]
    matched_bank_count = (
        session.scalar(
            select(func.count(distinct(Match.bank_transaction_id))).where(
                Match.job_id == job.id,
                Match.status.in_(active_statuses),
            )
        )
        or 0
    )
    matched_ledger_count = (
        session.scalar(
            select(func.count(distinct(Match.ledger_transaction_id))).where(
                Match.job_id == job.id,
                Match.status.in_(active_statuses),
            )
        )
        or 0
    )

    return ReconciliationSummaryResponse(
        job_id=job.id,
        status=JobStatus(job.status),
        bank_transaction_count=bank_count,
        ledger_transaction_count=ledger_count,
        matched_count=matched_count,
        under_review_count=under_review_count,
        reconciled_count=reconciled_count,
        rejected_count=rejected_count,
        unmatched_bank_count=max(bank_count - matched_bank_count, 0),
        unmatched_ledger_count=max(ledger_count - matched_ledger_count, 0),
    )


@router.post("", response_model=ReconciliationCreateResponse)
def create_reconciliation(
    bank_pdf: Annotated[UploadFile, File()],
    ledger_pdf: Annotated[UploadFile, File()],
    session: Annotated[Session, Depends(get_db_session)],
) -> ReconciliationCreateResponse:
    job_id = uuid.uuid4()
    bank_pdf_content = bank_pdf.file.read()
    ledger_pdf_content = ledger_pdf.file.read()

    try:
        bank_pdf_path = upload_statement_pdf_if_missing(bank_pdf_content, "bank")
        ledger_pdf_path = upload_statement_pdf_if_missing(
            ledger_pdf_content, "ledger"
        )

        job = ReconciliationJob(
            id=job_id,
            status=JobStatus.QUEUED.value,
            bank_pdf_path=bank_pdf_path,
            ledger_pdf_path=ledger_pdf_path,
        )
        session.add(job)
        session.commit()

        try:
            enqueue_reconciliation_job(str(job_id))
        except Exception as exc:
            job.status = JobStatus.FAILED.value
            job.error_message = f"Failed to enqueue reconciliation job: {exc}"
            session.commit()
            raise AppError(
                "Failed to queue reconciliation job", status_code=503
            ) from exc

        return ReconciliationCreateResponse(job_id=job_id, status=JobStatus.QUEUED)
    except AppError:
        raise
    except Exception as exc:
        session.rollback()
        logger.exception("Failed to create reconciliation job")
        raise AppError("Failed to create reconciliation job", status_code=500) from exc


@router.get("/{job_id}", response_model=ReconciliationDetailResponse)
def get_reconciliation(
    job_id: uuid.UUID,
    session: Annotated[Session, Depends(get_db_session)],
) -> ReconciliationDetailResponse:
    job = session.get(ReconciliationJob, job_id)
    if job is None:
        raise AppError("Reconciliation job not found", status_code=404)

    return ReconciliationDetailResponse(
        job=ReconciliationJobResponse.model_validate(job),
        summary=build_reconciliation_summary(session, job),
    )
