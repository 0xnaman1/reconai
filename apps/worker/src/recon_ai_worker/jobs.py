from datetime import UTC, datetime


def process_reconciliation_job(job_id: str) -> dict[str, str]:
    return {
        "job_id": job_id,
        "status": "processed",
        "processed_at": datetime.now(UTC).isoformat(),
    }
