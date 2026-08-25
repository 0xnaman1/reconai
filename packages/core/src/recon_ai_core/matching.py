from __future__ import annotations

import uuid
from dataclasses import dataclass

from rapidfuzz import fuzz
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from recon_ai_core.constants import MatchStatus, MatchType, TransactionSource
from recon_ai_core.models import Match, Transaction
from recon_ai_core.reporting import (
    ACTIVE_MATCH_STATUSES,
    list_unmatched_transactions,
)

AMOUNT_EXACT_POINTS = 40
DATE_EXACT_POINTS = 25
DATE_TOLERANCE_POINTS = {1: 20, 2: 18, 3: 15}
REFERENCE_EXACT_POINTS = 25
DESCRIPTION_MAX_POINTS = 10

AUTO_MATCH_THRESHOLD = 90
REVIEW_THRESHOLD = 70

# How many candidate counterparts to offer per unmatched transaction.
SUGGESTIONS_PER_TRANSACTION = 3


class MatchingError(Exception):
    """Raised when a requested match cannot be created."""


@dataclass(frozen=True)
class MatchSuggestion:
    """A possible counterpart for a transaction the engine left unmatched."""

    bank_transaction: Transaction
    ledger_transaction: Transaction
    score: int
    reason: str


@dataclass(frozen=True)
class MatchCandidate:
    """A scored bank/ledger pair that reached at least the review threshold."""

    bank_transaction: Transaction
    ledger_transaction: Transaction
    score: int
    match_type: MatchType
    status: MatchStatus
    reason: str


def _normalize_reference(reference: str | None) -> str | None:
    if reference is None:
        return None
    normalized = "".join(char for char in reference if char.isalnum()).upper()
    return normalized or None


def _description_similarity(bank: Transaction, ledger: Transaction) -> float:
    return fuzz.token_sort_ratio(bank.description.lower(), ledger.description.lower())


def _score_pair(bank: Transaction, ledger: Transaction) -> tuple[int, str, bool]:
    """Score one candidate pair.

    Returns the score, a human readable reason, and whether every strong signal
    (amount, date, reference) matched exactly.
    """
    score = 0
    reasons: list[str] = []

    amount_exact = bank.amount == ledger.amount
    if amount_exact:
        score += AMOUNT_EXACT_POINTS
        reasons.append("amount matched exactly")
    else:
        reasons.append("amounts differ")

    day_difference = abs((bank.transaction_date - ledger.transaction_date).days)
    date_exact = day_difference == 0
    if date_exact:
        score += DATE_EXACT_POINTS
        reasons.append("transaction dates matched")
    elif day_difference in DATE_TOLERANCE_POINTS:
        score += DATE_TOLERANCE_POINTS[day_difference]
        plural = "s" if day_difference > 1 else ""
        reasons.append(f"transaction dates differ by {day_difference} day{plural}")
    else:
        reasons.append(f"transaction dates differ by {day_difference} days")

    bank_reference = _normalize_reference(bank.reference_number)
    ledger_reference = _normalize_reference(ledger.reference_number)
    reference_exact = (
        bank_reference is not None and bank_reference == ledger_reference
    )
    if reference_exact:
        score += REFERENCE_EXACT_POINTS
        reasons.append("reference matched")
    elif bank_reference is None or ledger_reference is None:
        reasons.append("reference not available on both sides")
    else:
        reasons.append("references differ")

    similarity = _description_similarity(bank, ledger)
    score += round(similarity / 100 * DESCRIPTION_MAX_POINTS)
    reasons.append(f"descriptions are {round(similarity)}% similar")

    reason = ", ".join(reasons).capitalize() + "."
    return score, reason, amount_exact and date_exact and reference_exact


def _is_comparable(bank: Transaction, ledger: Transaction) -> bool:
    """Reject pairs whose currencies are known to disagree."""
    if bank.currency is None or ledger.currency is None:
        return True
    return bank.currency.upper() == ledger.currency.upper()


def match_transactions(
    bank_transactions: list[Transaction], ledger_transactions: list[Transaction]
) -> list[MatchCandidate]:
    """Pick the best one-to-one bank/ledger pairing above the review threshold.

    Every pair is scored, then pairs are claimed highest score first so a strong
    candidate is never lost to a weaker pair that happened to be scored earlier.
    Each transaction can appear in at most one match.
    """
    scored: list[tuple[int, int, int, Transaction, Transaction, str, bool]] = []
    for bank_index, bank in enumerate(bank_transactions):
        for ledger_index, ledger in enumerate(ledger_transactions):
            if not _is_comparable(bank, ledger):
                continue
            score, reason, strong_exact = _score_pair(bank, ledger)
            if score < REVIEW_THRESHOLD:
                continue
            scored.append(
                (-score, bank_index, ledger_index, bank, ledger, reason, strong_exact)
            )

    scored.sort(key=lambda item: item[:3])

    claimed_bank: set[int] = set()
    claimed_ledger: set[int] = set()
    candidates: list[MatchCandidate] = []
    for (
        negative_score,
        bank_index,
        ledger_index,
        bank,
        ledger,
        reason,
        strong_exact,
    ) in scored:
        if bank_index in claimed_bank or ledger_index in claimed_ledger:
            continue
        claimed_bank.add(bank_index)
        claimed_ledger.add(ledger_index)
        score = -negative_score
        candidates.append(
            MatchCandidate(
                bank_transaction=bank,
                ledger_transaction=ledger,
                score=score,
                match_type=MatchType.EXACT if strong_exact else MatchType.FUZZY,
                status=(
                    MatchStatus.MATCHED
                    if score >= AUTO_MATCH_THRESHOLD
                    else MatchStatus.UNDER_REVIEW
                ),
                reason=reason,
            )
        )
    return candidates


def replace_job_matches(session: Session, job_id: uuid.UUID) -> dict[str, int]:
    """Rebuild every match for a job from its stored transactions.

    Existing matches are dropped first so re-running a job cannot stack duplicate
    rows. Transactions below the review threshold are simply left unmatched.
    """
    transactions = session.scalars(
        select(Transaction)
        .where(Transaction.job_id == job_id)
        .order_by(Transaction.transaction_date, Transaction.created_at, Transaction.id)
    ).all()
    bank_transactions = [
        row for row in transactions if row.source == TransactionSource.BANK.value
    ]
    ledger_transactions = [
        row for row in transactions if row.source == TransactionSource.LEDGER.value
    ]

    session.execute(delete(Match).where(Match.job_id == job_id))

    candidates = match_transactions(bank_transactions, ledger_transactions)
    session.add_all(
        [
            Match(
                job_id=job_id,
                bank_transaction_id=candidate.bank_transaction.id,
                ledger_transaction_id=candidate.ledger_transaction.id,
                match_type=candidate.match_type.value,
                confidence_score=min(candidate.score, 100),
                status=candidate.status.value,
                reason=candidate.reason,
            )
            for candidate in candidates
        ]
    )

    matched = sum(1 for c in candidates if c.status is MatchStatus.MATCHED)
    under_review = len(candidates) - matched
    return {
        "matched": matched,
        "under_review": under_review,
        "unmatched_bank": len(bank_transactions) - len(candidates),
        "unmatched_ledger": len(ledger_transactions) - len(candidates),
    }


def suggest_matches(
    session: Session,
    job_id: uuid.UUID,
    limit_per_transaction: int = SUGGESTIONS_PER_TRANSACTION,
) -> list[MatchSuggestion]:
    """Rank possible counterparts for each bank transaction left unmatched.

    Automatic matching creates nothing below the review threshold, so these
    pairs scored under 70: close enough to be worth a reviewer's judgement, not
    close enough for the engine to assert. Ranking is per bank transaction
    rather than global because a reviewer works through them one at a time, and
    the same ledger row can be the best remaining guess for more than one.
    """
    unmatched = list_unmatched_transactions(session, job_id)
    bank_transactions = [
        row for row in unmatched if row.source == TransactionSource.BANK.value
    ]
    ledger_transactions = [
        row for row in unmatched if row.source == TransactionSource.LEDGER.value
    ]

    suggestions: list[MatchSuggestion] = []
    for bank in bank_transactions:
        scored: list[tuple[int, str, Transaction]] = []
        for ledger in ledger_transactions:
            if not _is_comparable(bank, ledger):
                continue
            score, reason, _ = _score_pair(bank, ledger)
            scored.append((score, reason, ledger))

        # Ties break on id so the same job always produces the same order.
        scored.sort(key=lambda item: (-item[0], str(item[2].id)))
        suggestions.extend(
            MatchSuggestion(
                bank_transaction=bank,
                ledger_transaction=ledger,
                score=score,
                reason=reason,
            )
            for score, reason, ledger in scored[:limit_per_transaction]
        )

    return suggestions


def _require_unclaimed(session: Session, transaction: Transaction) -> None:
    claimed = session.scalar(
        select(Match.id).where(
            Match.status.in_(ACTIVE_MATCH_STATUSES),
            (Match.bank_transaction_id == transaction.id)
            | (Match.ledger_transaction_id == transaction.id),
        )
    )
    if claimed is not None:
        raise MatchingError(
            f"Transaction {transaction.id} is already part of another match"
        )


def create_manual_match(
    session: Session,
    bank_transaction_id: uuid.UUID,
    ledger_transaction_id: uuid.UUID,
) -> Match:
    """Pair two unmatched transactions because a reviewer says they belong together.

    The pair is scored the same way the engine scores its own, so the stored
    confidence reflects how the data actually compares, but the status is
    reconciled outright: a human asserting the pairing is a stronger signal than
    any score, which is why the engine's thresholds are not consulted here.
    """
    bank = session.get(Transaction, bank_transaction_id)
    ledger = session.get(Transaction, ledger_transaction_id)
    if bank is None or ledger is None:
        raise MatchingError("Both transactions must exist")
    if bank.source != TransactionSource.BANK.value:
        raise MatchingError(f"Transaction {bank.id} is not a bank transaction")
    if ledger.source != TransactionSource.LEDGER.value:
        raise MatchingError(f"Transaction {ledger.id} is not a ledger transaction")
    if bank.job_id != ledger.job_id:
        raise MatchingError("Both transactions must belong to the same job")

    _require_unclaimed(session, bank)
    _require_unclaimed(session, ledger)

    score, reason, _ = _score_pair(bank, ledger)
    match = Match(
        job_id=bank.job_id,
        bank_transaction_id=bank.id,
        ledger_transaction_id=ledger.id,
        match_type=MatchType.MANUAL.value,
        confidence_score=min(max(score, 0), 100),
        status=MatchStatus.RECONCILED.value,
        reason=f"Reconciled by a reviewer. {reason}",
    )
    session.add(match)
    session.flush()
    return match
