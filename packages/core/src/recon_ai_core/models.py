from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from recon_ai_core.constants import (
    ChatRole,
    JobStatus,
    MatchStatus,
    MatchType,
    TransactionSource,
)
from recon_ai_core.database import Base


def _enum_values(enum_type: type) -> str:
    return ", ".join(f"'{item.value}'" for item in enum_type)


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )


class TimestampMixin(CreatedAtMixin):
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ReconciliationJob(TimestampMixin, Base):
    __tablename__ = "reconciliation_jobs"
    __table_args__ = (
        CheckConstraint(f"status in ({_enum_values(JobStatus)})", name="valid_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=JobStatus.QUEUED.value
    )
    bank_pdf_path: Mapped[str] = mapped_column(Text, nullable=False)
    ledger_pdf_path: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)

    transactions: Mapped[list[Transaction]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    matches: Mapped[list[Match]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    chat_sessions: Mapped[list[ChatSession]] = relationship(back_populates="active_job")
    agent_actions: Mapped[list[AgentAction]] = relationship(back_populates="job")


class Transaction(CreatedAtMixin, Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint(
            f"source in ({_enum_values(TransactionSource)})", name="valid_source"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reconciliation_jobs.id"), nullable=False
    )
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    reference_number: Mapped[str | None] = mapped_column(Text)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(8))
    raw_text: Mapped[str | None] = mapped_column(Text)
    extra_data: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )

    job: Mapped[ReconciliationJob] = relationship(back_populates="transactions")
    bank_matches: Mapped[list[Match]] = relationship(
        back_populates="bank_transaction",
        foreign_keys="Match.bank_transaction_id",
    )
    ledger_matches: Mapped[list[Match]] = relationship(
        back_populates="ledger_transaction",
        foreign_keys="Match.ledger_transaction_id",
    )


class Match(TimestampMixin, Base):
    __tablename__ = "matches"
    __table_args__ = (
        CheckConstraint(
            f"match_type in ({_enum_values(MatchType)})", name="valid_match_type"
        ),
        CheckConstraint(
            f"status in ({_enum_values(MatchStatus)})", name="valid_status"
        ),
        CheckConstraint(
            "confidence_score >= 0 and confidence_score <= 100",
            name="valid_confidence_score",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reconciliation_jobs.id"), nullable=False
    )
    bank_transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False
    )
    ledger_transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False
    )
    match_type: Mapped[str] = mapped_column(String(16), nullable=False)
    confidence_score: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    job: Mapped[ReconciliationJob] = relationship(back_populates="matches")
    bank_transaction: Mapped[Transaction] = relationship(
        back_populates="bank_matches", foreign_keys=[bank_transaction_id]
    )
    ledger_transaction: Mapped[Transaction] = relationship(
        back_populates="ledger_matches", foreign_keys=[ledger_transaction_id]
    )


class ChatSession(TimestampMixin, Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    active_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reconciliation_jobs.id")
    )

    active_job: Mapped[ReconciliationJob | None] = relationship(
        back_populates="chat_sessions"
    )
    messages: Mapped[list[ChatMessage]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    agent_actions: Mapped[list[AgentAction]] = relationship(back_populates="session")


class ChatMessage(CreatedAtMixin, Base):
    __tablename__ = "chat_messages"
    __table_args__ = (
        CheckConstraint(f"role in ({_enum_values(ChatRole)})", name="valid_role"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    extra_data: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )

    session: Mapped[ChatSession] = relationship(back_populates="messages")


class AgentAction(CreatedAtMixin, Base):
    __tablename__ = "agent_actions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_sessions.id")
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reconciliation_jobs.id")
    )
    tool_name: Mapped[str] = mapped_column(String(128), nullable=False)
    tool_input: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    tool_output: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    session: Mapped[ChatSession | None] = relationship(back_populates="agent_actions")
    job: Mapped[ReconciliationJob | None] = relationship(back_populates="agent_actions")
