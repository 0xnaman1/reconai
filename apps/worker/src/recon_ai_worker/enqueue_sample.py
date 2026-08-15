import uuid

from recon_ai_core.queue import enqueue_reconciliation_job


def main() -> None:
    job_id = str(uuid.uuid4())
    rq_job = enqueue_reconciliation_job(job_id)
    print(f"enqueued {rq_job.id} for reconciliation job {job_id}")


if __name__ == "__main__":
    main()
