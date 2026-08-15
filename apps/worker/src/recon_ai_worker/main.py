from recon_ai_core.queue import (
    QUEUE_NAME,
    get_reconciliation_queue,
    get_redis_connection,
)
from rq import Worker


def main() -> None:
    queue = get_reconciliation_queue()
    worker = Worker([queue], connection=get_redis_connection())
    print(f"Recon AI worker listening on queue: {QUEUE_NAME}")
    worker.work()


if __name__ == "__main__":
    main()
