from __future__ import annotations

import uuid
from hashlib import sha256
from typing import Literal

from recon_ai_core.settings import get_settings
from recon_ai_core.supabase_client import get_supabase_client

StatementKind = Literal["bank", "ledger"]


def build_reconciliation_pdf_path(job_id: str | uuid.UUID, kind: StatementKind) -> str:
    return f"reconciliations/{job_id}/{kind}.pdf"


def build_statement_pdf_path(content: bytes, kind: StatementKind) -> str:
    digest = sha256(content).hexdigest()
    return f"statements/{kind}/{digest}.pdf"


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


def file_exists(storage_path: str) -> bool:
    bucket = get_settings().supabase_storage_bucket
    return get_supabase_client().storage.from_(bucket).exists(storage_path)


def _is_duplicate_storage_error(exc: Exception) -> bool:
    if getattr(exc, "status", None) == 409 or getattr(exc, "status_code", None) == 409:
        return True
    message = str(exc).lower()
    return "duplicate" in message or "already exists" in message


def upload_pdf_bytes_if_missing(storage_path: str, content: bytes) -> tuple[str, bool]:
    if file_exists(storage_path):
        return storage_path, False
    try:
        return upload_pdf_bytes(storage_path, content), True
    except Exception as exc:
        if _is_duplicate_storage_error(exc):
            return storage_path, False
        raise


def upload_statement_pdf_if_missing(
    content: bytes, kind: StatementKind
) -> str:
    storage_path = build_statement_pdf_path(content, kind)
    upload_pdf_bytes_if_missing(storage_path, content)
    return storage_path


def download_file_bytes(storage_path: str) -> bytes:
    bucket = get_settings().supabase_storage_bucket
    return get_supabase_client().storage.from_(bucket).download(storage_path)


def delete_files(storage_paths: list[str]) -> None:
    if not storage_paths:
        return
    bucket = get_settings().supabase_storage_bucket
    get_supabase_client().storage.from_(bucket).remove(storage_paths)
