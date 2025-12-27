from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional, List, Dict

class ReviewSummary(BaseModel):
    id: UUID4
    album_name: str
    artist_name: str
    cover_url: Optional[str] = None
    average_score: float
    tier: str
    created_at: datetime

    class Config:
        from_attributes = True

class CalendarResponse(BaseModel):
    month: int
    year: int
    days: Dict[str, List[ReviewSummary]]