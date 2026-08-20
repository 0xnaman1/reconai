from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class PdfExtractionError(Exception):
    """Raised when text cannot be extracted from a PDF."""


def extract_pdf_text(content: bytes, *, label: str = "PDF") -> str:
    """Extract text from every page of a text-based PDF.

    Raises PdfExtractionError when the file cannot be parsed or contains no text.
    """
    if not content:
        raise PdfExtractionError(f"{label} is empty")

    try:
        reader = PdfReader(BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
    except PdfReadError as exc:
        raise PdfExtractionError(f"{label} could not be parsed: {exc}") from exc
    except Exception as exc:
        raise PdfExtractionError(f"{label} could not be read: {exc}") from exc

    if not pages:
        raise PdfExtractionError(f"{label} has no pages")

    text = "\n".join(pages).strip()
    if not text:
        raise PdfExtractionError(
            f"{label} has no extractable text; scanned PDFs are not supported"
        )
    return text
