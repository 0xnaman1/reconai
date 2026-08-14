from recon_ai_core.settings import get_settings
from redis import Redis
from rq import Queue

QUEUE_NAME = "reconciliation"


def get_redis_connection() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.redis_url)


def get_queue() -> Queue:
    return Queue(QUEUE_NAME, connection=get_redis_connection())


def enqueue_reconciliation_job(job_id: str):
    queue = get_queue()
    return queue.enqueue("recon_ai_worker.jobs.process_reconciliation_job", job_id)
