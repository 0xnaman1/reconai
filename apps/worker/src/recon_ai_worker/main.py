import os
import sys

from recon_ai_core.queue import (
    QUEUE_NAME,
    get_reconciliation_queue,
    get_redis_connection,
)
from rq import Worker

FORK_SAFETY_ENV_VAR = "OBJC_DISABLE_INITIALIZE_FORK_SAFETY"


def _ensure_macos_fork_safety() -> None:
    """Re-exec with ObjC fork safety disabled on macOS.

    RQ forks a work horse per job. On macOS the Objective-C runtime aborts the
    forked child (SIGABRT) when a library such as httpx or redis has already
    initialized it in the parent. The runtime reads this variable at process
    start, so it must be set before the interpreter launches.
    """
    if sys.platform != "darwin" or os.environ.get(FORK_SAFETY_ENV_VAR):
        return
    os.execve(
        sys.executable,
        [sys.executable, *sys.argv],
        {**os.environ, FORK_SAFETY_ENV_VAR: "YES"},
    )


def main() -> None:
    _ensure_macos_fork_safety()
    queue = get_reconciliation_queue()
    worker = Worker([queue], connection=get_redis_connection())
    print(f"Recon AI worker listening on queue: {QUEUE_NAME}")
    worker.work()


if __name__ == "__main__":
    main()
