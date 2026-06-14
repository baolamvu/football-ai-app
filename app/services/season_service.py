from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models import Season
from app.repositories import league_repo, season_repo


def list_seasons_for_league(db: Session, league_id: int) -> list[Season]:
    if league_repo.get_by_id(db, league_id) is None:
        raise NotFoundError("League not found")
    return season_repo.list_by_league_id(db, league_id)


def get_season(db: Session, season_id: int) -> Season:
    season = season_repo.get_by_id(db, season_id)
    if season is None:
        raise NotFoundError("Season not found")
    return season
