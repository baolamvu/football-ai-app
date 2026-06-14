from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Season


def list_by_league_id(db: Session, league_id: int) -> list[Season]:
    stmt = select(Season).where(Season.league_id == league_id).order_by(Season.start_date.desc())
    return list(db.scalars(stmt).all())


def get_by_id(db: Session, season_id: int) -> Season | None:
    return db.get(Season, season_id)
