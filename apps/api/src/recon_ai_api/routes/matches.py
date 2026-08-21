from __future__ import annotations

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from recon_ai_core.constants import MatchStatus
from recon_ai_core.models import Match
from recon_ai_core.schemas import MatchResponse
from sqlalchemy.orm import Session

from recon_ai_api.dependencies import get_db_session
from recon_ai_api.errors import AppError

router = APIRouter(prefix="/matches", tags=["matches"])
logger = logging.getLogger(__name__)


def _record_review(
    session: Session, match_id: uuid.UUID, status: MatchStatus
) -> MatchResponse:
    """Record a reviewer's decision on one match.

    Both auto matches and under-review matches can be reviewed: a reviewer who
    spots a wrong auto match needs to be able to reject it.
    """
    match = session.get(Match, match_id)
    if match is None:
        raise AppError("Match not found", status_code=404)

    match.status = status.value
    session.commit()
    session.refresh(match)

    return MatchResponse.model_validate(match)


@router.post("/{match_id}/approve", response_model=MatchResponse)
def approve_match(
    match_id: uuid.UUID,
    session: Annotated[Session, Depends(get_db_session)],
) -> MatchResponse:
    """Confirm that a match pairs the same real transaction."""
    return _record_review(session, match_id, MatchStatus.RECONCILED)


@router.post("/{match_id}/reject", response_model=MatchResponse)
def reject_match(
    match_id: uuid.UUID,
    session: Annotated[Session, Depends(get_db_session)],
) -> MatchResponse:
    """Record that a match does not pair the same real transaction."""
    return _record_review(session, match_id, MatchStatus.REJECTED)
