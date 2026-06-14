from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.match import MatchOut
from app.schemas.season import SeasonOut
from app.services import match_service, season_service

router = APIRouter(prefix="/seasons", tags=["seasons"])


@router.get("/{season_id}", response_model=SeasonOut)
def get_season(season_id: int, db: Session = Depends(get_db)):
    return season_service.get_season(db, season_id)


@router.get("/{season_id}/matches", response_model=list[MatchOut])
def list_season_matches(
    season_id: int,
    status: str | None = Query(default=None, description="scheduled | finished | live | ..."),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return match_service.list_matches(
        db,
        season_id=season_id,
        status=status,
        from_date=from_date,
        to_date=to_date,
    )
