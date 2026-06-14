from typing import Literal, Optional

from pydantic import BaseModel, Field


class PredictionOut(BaseModel):
    match_id: int
    home_team: str
    away_team: str
    home_win: float = Field(..., description="Home win probability (percent)")
    draw: float
    away_win: float
    model_name: str
    source: Literal["stored", "computed"]
    notes: Optional[str] = None
