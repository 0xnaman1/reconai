from collections.abc import Iterator

from recon_ai_core.database import get_session_factory
from sqlalchemy.orm import Session


def get_db_session() -> Iterator[Session]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
