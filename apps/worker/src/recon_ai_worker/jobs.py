from __future__ import annotations

import logging
import uuid

from recon_ai_core.constants import JobStatus, TransactionSource
from recon_ai_core.database import session_scope
from recon_ai_core.extraction import ExtractionError, extract_transactions
from recon_ai_core.models import ReconciliationJob
from recon_ai_core.pdf import PdfExtractionError, extract_pdf_text
from recon_ai_core.storage import download_file_bytes
from recon_ai_core.transactions import replace_job_transactions

logger = logging.getLogger(__name__)


class ReconciliationJobError(Exception):
    """Raised when a reconciliation job cannot be processed."""


def _set_job_status(job_id: uuid.UUID, status: JobStatus) -> ReconciliationJob:
    with session_scope() as session:
        job = session.get(ReconciliationJob, job_id)
        if job is None:
            raise ReconciliationJobError(f"Reconciliation job {job_id} not found")
        job.status = status.value
        job.error_message = None
        session.flush()
        return job


def _fail_job(job_id: uuid.UUID, message: str) -> None:
    with session_scope() as session:
        job = session.get(ReconciliationJob, job_id)
        if job is None:
            return
        job.status = JobStatus.FAILED.value
        job.error_message = message


def process_reconciliation_job(job_id: str) -> dict[str, object]:
    parsed_job_id = uuid.UUID(job_id)
    job = _set_job_status(parsed_job_id, JobStatus.EXTRACTING)

    try:
        bank_text = extract_pdf_text(
            download_file_bytes(job.bank_pdf_path), label="Bank statement PDF"
        )
        ledger_text = extract_pdf_text(
            download_file_bytes(job.ledger_pdf_path), label="Ledger statement PDF"
        )
    except PdfExtractionError as exc:
        _fail_job(parsed_job_id, str(exc))
        logger.warning("PDF extraction failed for job %s: %s", job_id, exc)
        raise
    except Exception as exc:
        _fail_job(parsed_job_id, f"Failed to read statement PDFs: {exc}")
        logger.exception("Failed to read statement PDFs for job %s", job_id)
        raise

    try:
        bank_transactions = extract_transactions(bank_text, TransactionSource.BANK)
        ledger_transactions = extract_transactions(ledger_text, TransactionSource.LEDGER)
    except ExtractionError as exc:
        _fail_job(parsed_job_id, str(exc))
        logger.warning("Transaction extraction failed for job %s: %s", job_id, exc)
        raise
    except Exception as exc:
        _fail_job(parsed_job_id, f"Failed to extract transactions: {exc}")
        logger.exception("Failed to extract transactions for job %s", job_id)
        raise

    try:
        with session_scope() as session:
            counts = replace_job_transactions(
                session, parsed_job_id, bank_transactions, ledger_transactions
            )
    except Exception as exc:
        _fail_job(parsed_job_id, f"Failed to store transactions: {exc}")
        logger.exception("Failed to store transactions for job %s", job_id)
        raise

    return {
        "job_id": job_id,
        "status": JobStatus.EXTRACTING.value,
        "bank_transaction_count": counts[TransactionSource.BANK.value],
        "ledger_transaction_count": counts[TransactionSource.LEDGER.value],
    }
