from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from recon_ai_core.constants import (
    ChatRole,
    JobStatus,
    MatchStatus,
    MatchType,
    TransactionSource,
)


class ExtractedTransaction(BaseModel):
    transaction_date: date
    description: str = Field(min_length=1)
    amount: Decimal
    currency: str | None = None
    reference_number: str | None = None
    raw_text: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExtractedTransactionsResponse(BaseModel):
    transactions: list[ExtractedTransaction]


class ReconciliationJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: JobStatus
    bank_pdf_path: str
    ledger_pdf_path: str
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    source: TransactionSource
    transaction_date: date
    description: str
    reference_number: str | None = None
    amount: Decimal
    currency: str | None = None
    raw_text: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict, alias="extra_data")
    created_at: datetime


class MatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    bank_transaction_id: uuid.UUID
    ledger_transaction_id: uuid.UUID
    match_type: MatchType
    confidence_score: int
    status: MatchStatus
    reason: str
    created_at: datetime
    updated_at: datetime


class ReconciliationSummaryResponse(BaseModel):
    job_id: uuid.UUID
    status: JobStatus
    bank_transaction_count: int = 0
    ledger_transaction_count: int = 0
    matched_count: int = 0
    under_review_count: int = 0
    reconciled_count: int = 0
    rejected_count: int = 0
    unmatched_bank_count: int = 0
    unmatched_ledger_count: int = 0


class ChatSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    active_job_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    role: ChatRole
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict, alias="extra_data")
    created_at: datetime


class AgentActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID | None = None
    job_id: uuid.UUID | None = None
    tool_name: str
    tool_input: dict[str, Any]
    tool_output: dict[str, Any]
    created_at: datetime
