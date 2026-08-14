from __future__ import annotations

import uuid
from typing import Literal

from recon_ai_core.settings import get_settings
from recon_ai_core.supabase_client import get_supabase_client

StatementKind = Literal["bank", "ledger"]


def build_reconciliation_pdf_path(job_id: str | uuid.UUID, kind: StatementKind) -> str:
    return f"reconciliations/{job_id}/{kind}.pdf"


def upload_pdf_bytes(storage_path: str, content: bytes, *, upsert: bool = False) -> str:
    bucket = get_settings().supabase_storage_bucket
    get_supabase_client().storage.from_(bucket).upload(
        storage_path,
        content,
        file_options={
            "content-type": "application/pdf",
            "upsert": str(upsert).lower(),
        },
    )
    return storage_path


def download_file_bytes(storage_path: str) -> bytes:
    bucket = get_settings().supabase_storage_bucket
    return get_supabase_client().storage.from_(bucket).download(storage_path)


def delete_files(storage_paths: list[str]) -> None:
    if not storage_paths:
        return
    bucket = get_settings().supabase_storage_bucket
    get_supabase_client().storage.from_(bucket).remove(storage_paths)
