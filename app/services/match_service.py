from datetime import date

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, NotFoundError
from app.repositories import season_repo
from app.repositories.match_repo import MatchListFilters
from app.repositories.match_repo import get_by_id as get_match_row
from app.repositories.match_repo import list_matches as list_match_rows


def list_matches(
    db: Session,
    *,
    league_id: int | None = None,
    season_id: int | None = None,
    status: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
) -> list[dict]:
    if season_id is not None and season_repo.get_by_id(db, season_id) is None:
        raise NotFoundError("Season not found")
    if from_date and to_date and from_date > to_date:
        raise BadRequestError("from_date must be on or before to_date")

    filters = MatchListFilters(
        league_id=league_id,
        season_id=season_id,
        status=status,
        from_date=from_date,
        to_date=to_date,
    )
    return list_match_rows(db, filters)


def get_match(db: Session, match_id: int) -> dict:
    row = get_match_row(db, match_id)
    if row is None:
        raise NotFoundError("Match not found")
    return row
