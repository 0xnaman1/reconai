import uuid

from recon_ai_core.storage import (
    build_reconciliation_pdf_path,
    delete_files,
    download_file_bytes,
    upload_pdf_bytes,
)


def main() -> None:
    job_id = uuid.uuid4()
    storage_path = build_reconciliation_pdf_path(job_id, "bank")
    content = b"%PDF-1.4\n% Recon AI storage verification\n"

    try:
        upload_pdf_bytes(storage_path, content)
        downloaded = download_file_bytes(storage_path)
        if downloaded != content:
            raise RuntimeError("Downloaded content does not match uploaded content")
        print(f"storage upload/download: ok ({storage_path})")
    finally:
        print("file uploaded")
        delete_files([storage_path])


if __name__ == "__main__":
    main()
