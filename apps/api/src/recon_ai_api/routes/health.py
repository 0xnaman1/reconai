from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from recon_ai_api.dependencies import get_db_session

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/db")
def database_health(session: Annotated[Session, Depends(get_db_session)]) -> dict[str, str]:
    session.execute(text("select 1"))
    return {"status": "ok"}
