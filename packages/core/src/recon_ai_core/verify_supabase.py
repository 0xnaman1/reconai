from __future__ import annotations

import sys
from collections.abc import Callable

from sqlalchemy import create_engine, text
from supabase import create_client

from recon_ai_core.settings import Settings, get_settings


def _require(value: str, name: str) -> None:
    if not value or value.startswith("your-") or "<" in value:
        raise RuntimeError(f"{name} is missing or still contains a placeholder")


def verify_database(settings: Settings) -> None:
    _require(settings.database_url, "DATABASE_URL")
    engine = create_engine(settings.database_url)

    with engine.connect() as connection:
        connection.execute(text("select 1"))


def verify_storage(settings: Settings) -> None:
    _require(settings.supabase_url, "SUPABASE_URL")
    _require(settings.supabase_secret_key, "SUPABASE_SECRET_KEY")
    _require(settings.supabase_storage_bucket, "SUPABASE_STORAGE_BUCKET")

    client = create_client(settings.supabase_url, settings.supabase_secret_key)
    buckets = client.storage.list_buckets()
    bucket_names = {
        bucket.get("name") if isinstance(bucket, dict) else bucket.name
        for bucket in buckets
    }

    if settings.supabase_storage_bucket not in bucket_names:
        raise RuntimeError(
            f"Storage bucket {settings.supabase_storage_bucket!r} was not found"
        )


def _run_check(
    name: str, check: Callable[[Settings], None], settings: Settings
) -> bool:
    try:
        check(settings)
    except Exception as exc:
        print(f"{name}: failed - {exc}")
        return False

    print(f"{name}: ok")
    return True


def main() -> None:
    settings = get_settings()
    results = [
        _run_check("database", verify_database, settings),
        _run_check("storage", verify_storage, settings),
    ]
    if not all(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
