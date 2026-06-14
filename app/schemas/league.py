from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class LeagueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    country: Optional[str] = None
    tier: Optional[int] = None
    created_at: datetime
