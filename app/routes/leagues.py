from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.league import LeagueOut
from app.schemas.season import SeasonOut
from app.services import league_service, season_service

router = APIRouter(prefix="/leagues", tags=["leagues"])


@router.get("", response_model=list[LeagueOut])
def list_leagues(db: Session = Depends(get_db)):
    return league_service.list_leagues(db)


@router.get("/{league_id}", response_model=LeagueOut)
def get_league(league_id: int, db: Session = Depends(get_db)):
    return league_service.get_league(db, league_id)


@router.get("/{league_id}/seasons", response_model=list[SeasonOut])
def list_league_seasons(league_id: int, db: Session = Depends(get_db)):
    return season_service.list_seasons_for_league(db, league_id)
