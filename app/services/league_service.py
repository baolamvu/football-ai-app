from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models import League
from app.repositories import league_repo


def list_leagues(db: Session) -> list[League]:
    return league_repo.list_all(db)


def get_league(db: Session, league_id: int) -> League:
    league = league_repo.get_by_id(db, league_id)
    if league is None:
        raise NotFoundError("League not found")
    return league
