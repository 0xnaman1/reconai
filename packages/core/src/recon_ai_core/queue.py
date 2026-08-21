from redis import Redis
from rq import Queue

from recon_ai_core.settings import get_settings

QUEUE_NAME = "reconciliation"
RECONCILIATION_JOB_TARGET = "recon_ai_worker.jobs.process_reconciliation_job"


def get_redis_connection() -> Redis:
    # Bound the connect attempt so an unreachable Redis fails fast instead of
    # hanging whoever is enqueueing. Only the connect is bounded: the worker's
    # blocking pop needs reads to wait indefinitely.
    return Redis.from_url(get_settings().redis_url, socket_connect_timeout=5)


def get_reconciliation_queue() -> Queue:
    return Queue(QUEUE_NAME, connection=get_redis_connection())


def enqueue_reconciliation_job(job_id: str):
    return get_reconciliation_queue().enqueue(RECONCILIATION_JOB_TARGET, job_id)
