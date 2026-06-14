from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SeasonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    league_id: int
    name: str
    start_date: date
    end_date: date
    matchweeks: Optional[int] = None
    created_at: datetime
