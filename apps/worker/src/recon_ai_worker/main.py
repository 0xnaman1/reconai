from rq import Worker

from recon_ai_worker.queue import QUEUE_NAME, get_queue, get_redis_connection


def main() -> None:
    queue = get_queue()
    worker = Worker([queue], connection=get_redis_connection())
    print(f"Recon AI worker listening on queue: {QUEUE_NAME}")
    worker.work()


if __name__ == "__main__":
    main()
