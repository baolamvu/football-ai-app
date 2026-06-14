from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.schemas.match import MatchDetailOut, MatchOut
from app.schemas.prediction import PredictionOut
from app.services import match_service, prediction_service

router = APIRouter(prefix="/matches", tags=["matches"])

VALID_STATUSES = frozenset({"scheduled", "live", "finished", "postponed", "cancelled"})


@router.get("", response_model=list[MatchOut])
def list_matches(
    league_id: int | None = Query(default=None, description="Filter by league id"),
    season_id: int | None = Query(default=None, description="Filter by season id"),
    status: str | None = Query(default=None, description="Match status filter"),
    from_date: date | None = Query(default=None, description="Kickoff on or after (UTC date)"),
    to_date: date | None = Query(default=None, description="Kickoff on or before (UTC date)"),
    db: Session = Depends(get_db),
):
    if status is not None and status not in VALID_STATUSES:
        from app.core.exceptions import BadRequestError

        raise BadRequestError(f"status must be one of: {', '.join(sorted(VALID_STATUSES))}")
    return match_service.list_matches(
        db,
        league_id=league_id,
        season_id=season_id,
        status=status,
        from_date=from_date,
        to_date=to_date,
    )


@router.get("/{match_id}", response_model=MatchDetailOut)
def get_match(match_id: int, db: Session = Depends(get_db)):
    return match_service.get_match(db, match_id)


@router.get("/{match_id}/prediction", response_model=PredictionOut)
def get_match_prediction(match_id: int, db: Session = Depends(get_db)):
    try:
        return prediction_service.compute_prediction(db, match_id)
    except ValueError as e:
        if str(e) == "match_not_found":
            raise NotFoundError("Match not found") from e
        raise
