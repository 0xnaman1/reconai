from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from openai import OpenAIError
from pydantic import BaseModel, Field, ValidationError

from recon_ai_core.constants import TransactionSource
from recon_ai_core.openai_client import get_openai_client
from recon_ai_core.schemas import ExtractedTransaction
from recon_ai_core.settings import get_settings


class ExtractionError(Exception):
    """Raised when statement text cannot be turned into valid transactions."""


class BankStatementRow(BaseModel):
    """One bank statement row, kept close to the source columns."""

    transaction_date: str = Field(description="Transaction date as YYYY-MM-DD")
    description: str
    reference_number: str | None
    withdrawal_amount: str | None = Field(
        description="Positive decimal string when the row is a withdrawal, else null"
    )
    deposit_amount: str | None = Field(
        description="Positive decimal string when the row is a deposit, else null"
    )
    closing_balance: str | None
    currency: str | None
    raw_text: str | None


class LedgerRow(BaseModel):
    """One general ledger row, kept close to the source columns."""

    transaction_date: str = Field(description="Transaction date as YYYY-MM-DD")
    description: str = Field(description="Transaction details")
    reference_number: str | None
    amount: str = Field(description="Signed decimal string, negative for money out")
    notes_and_tags: str | None
    currency: str | None
    raw_text: str | None


class BankStatementRows(BaseModel):
    transactions: list[BankStatementRow]


class LedgerRows(BaseModel):
    transactions: list[LedgerRow]


SYSTEM_PROMPT = (
    "You extract transaction rows from statement text. "
    "Return every transaction row exactly once, in the order it appears. "
    "Never invent rows, never merge rows, and never include opening balance, "
    "closing balance, subtotal, or carried-forward lines as transactions. "
    "Write amounts as plain decimal strings without currency symbols, "
    "thousands separators, or trailing text. "
    "Write dates as YYYY-MM-DD, inferring the year from the statement when a row "
    "omits it. Use null for any field the row does not provide. "
    "Copy the original line of the source text into raw_text."
)

BANK_PROMPT = (
    "Extract every transaction from this bank statement.\n\n"
    "Each row has a date, description, optional reference number, and an amount in "
    "either the withdrawal column or the deposit column. Put the amount in "
    "withdrawal_amount for money leaving the account and in deposit_amount for money "
    "entering it. Set exactly one of the two and leave the other null. Both values "
    "must be positive; the direction is carried by which field you fill.\n\n"
    "Record the row's closing balance in closing_balance when the statement shows one.\n\n"
    "Bank statement text:\n\n{text}"
)

LEDGER_PROMPT = (
    "Extract every transaction from this general ledger statement.\n\n"
    "Each row has a date, transaction details, an amount, and optional notes and tags. "
    "Keep the amount signed as the ledger presents it: negative for money out, "
    "positive for money in. Put the transaction details in description and any notes "
    "or tags in notes_and_tags.\n\n"
    "Ledger statement text:\n\n{text}"
)


def _parse_decimal(value: str, field: str, row: int) -> Decimal:
    cleaned = value.strip().replace(",", "").replace("$", "")
    try:
        return Decimal(cleaned)
    except (InvalidOperation, ValueError) as exc:
        raise ExtractionError(
            f"Row {row}: {field} is not a valid amount: {value!r}"
        ) from exc


def _parse_date(value: str, row: int) -> date:
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ExtractionError(
            f"Row {row}: transaction_date is not a valid date: {value!r}"
        ) from exc


def _normalize_bank_row(bank_row: BankStatementRow, row: int) -> ExtractedTransaction:
    """Collapse the withdrawal and deposit columns into one signed amount."""
    withdrawal = (
        _parse_decimal(bank_row.withdrawal_amount, "withdrawal_amount", row)
        if bank_row.withdrawal_amount
        else None
    )
    deposit = (
        _parse_decimal(bank_row.deposit_amount, "deposit_amount", row)
        if bank_row.deposit_amount
        else None
    )

    if withdrawal is not None and deposit is not None:
        raise ExtractionError(
            f"Row {row}: both withdrawal_amount and deposit_amount are set"
        )
    if withdrawal is None and deposit is None:
        raise ExtractionError(
            f"Row {row}: neither withdrawal_amount nor deposit_amount is set"
        )

    amount = -abs(withdrawal) if withdrawal is not None else abs(deposit)  # type: ignore[arg-type]

    metadata: dict[str, str] = {}
    if bank_row.closing_balance:
        metadata["closing_balance"] = bank_row.closing_balance.strip()

    return ExtractedTransaction(
        transaction_date=_parse_date(bank_row.transaction_date, row),
        description=bank_row.description.strip(),
        amount=amount,
        currency=bank_row.currency,
        reference_number=bank_row.reference_number,
        raw_text=bank_row.raw_text,
        metadata=metadata,
    )


def _normalize_ledger_row(ledger_row: LedgerRow, row: int) -> ExtractedTransaction:
    """Keep the ledger's own sign convention."""
    metadata: dict[str, str] = {}
    if ledger_row.notes_and_tags:
        metadata["notes_and_tags"] = ledger_row.notes_and_tags.strip()

    return ExtractedTransaction(
        transaction_date=_parse_date(ledger_row.transaction_date, row),
        description=ledger_row.description.strip(),
        amount=_parse_decimal(ledger_row.amount, "amount", row),
        currency=ledger_row.currency,
        reference_number=ledger_row.reference_number,
        raw_text=ledger_row.raw_text,
        metadata=metadata,
    )


def _parse_statement(prompt: str, response_model: type[BaseModel], label: str):
    client = get_openai_client()
    try:
        completion = client.chat.completions.parse(
            model=get_settings().openai_extraction_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format=response_model,
        )
    except OpenAIError as exc:
        raise ExtractionError(f"{label} extraction request failed: {exc}") from exc
    except ValidationError as exc:
        raise ExtractionError(
            f"{label} extraction returned rows that failed validation: {exc}"
        ) from exc

    message = completion.choices[0].message
    if message.refusal:
        raise ExtractionError(f"{label} extraction was refused: {message.refusal}")
    if message.parsed is None:
        raise ExtractionError(f"{label} extraction returned no structured output")
    return message.parsed


def extract_transactions(
    text: str, source: TransactionSource
) -> list[ExtractedTransaction]:
    """Turn statement text into validated, sign-normalized transactions."""
    if source is TransactionSource.BANK:
        prompt, response_model, label = (
            BANK_PROMPT.format(text=text),
            BankStatementRows,
            "Bank statement",
        )
    else:
        prompt, response_model, label = (
            LEDGER_PROMPT.format(text=text),
            LedgerRows,
            "Ledger statement",
        )

    parsed = _parse_statement(prompt, response_model, label)

    normalize = (
        _normalize_bank_row
        if source is TransactionSource.BANK
        else _normalize_ledger_row
    )
    try:
        transactions = [
            normalize(row, index)  # type: ignore[arg-type]
            for index, row in enumerate(parsed.transactions, start=1)
        ]
    except ExtractionError as exc:
        raise ExtractionError(f"{label} extraction produced invalid data. {exc}") from exc

    if not transactions:
        raise ExtractionError(f"{label} extraction found no transactions")
    return transactions
