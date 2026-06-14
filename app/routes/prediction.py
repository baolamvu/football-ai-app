"""Legacy query-param endpoint; prefer GET /matches/{match_id}/prediction."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models import Match, Team
from app.db.session import get_db
from app.schemas.prediction import PredictionOut
from app.services import prediction_service

router = APIRouter(prefix="/prediction", tags=["prediction"])


@router.get("", response_model=PredictionOut)
def get_prediction_by_teams(
    home: str = Query(..., description="Home team name (canonical)"),
    away: str = Query(..., description="Away team name (canonical)"),
    db: Session = Depends(get_db),
):
    home_team = db.scalars(select(Team).where(Team.canonical_name == home)).first()
    away_team = db.scalars(select(Team).where(Team.canonical_name == away)).first()
    if not home_team or not away_team:
        raise NotFoundError("Team not found")

    match = db.scalars(
        select(Match)
        .where(
            Match.home_team_id == home_team.id,
            Match.away_team_id == away_team.id,
        )
        .order_by(Match.kickoff_at.desc())
    ).first()
    if not match:
        raise NotFoundError("Match not found for these teams")

    return prediction_service.compute_prediction(db, match.id)
