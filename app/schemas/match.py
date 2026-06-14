from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MatchOut(BaseModel):
    id: int
    season_id: int
    league_id: int
    league_name: str
    league_code: str
    season_name: str
    matchweek: Optional[int] = None
    kickoff_at: datetime
    status: str
    home_team_id: int
    home_team: str
    away_team_id: int
    away_team: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None


class MatchDetailOut(MatchOut):
    competition_phase: Optional[str] = None
    neutral_site: bool = False
