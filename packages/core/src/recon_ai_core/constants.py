from enum import StrEnum


class TransactionSource(StrEnum):
    BANK = "bank"
    LEDGER = "ledger"


class JobStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    EXTRACTING = "extracting"
    MATCHING = "matching"
    COMPLETED = "completed"
    FAILED = "failed"


class MatchType(StrEnum):
    EXACT = "exact"
    FUZZY = "fuzzy"
    MANUAL = "manual"


class MatchStatus(StrEnum):
    MATCHED = "matched"
    UNDER_REVIEW = "under_review"
    RECONCILED = "reconciled"
    REJECTED = "rejected"


class ChatRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
