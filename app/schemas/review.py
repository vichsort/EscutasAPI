from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional, List, Dict

class TrackSchema(BaseModel):
    id: UUID4
    track_name: str
    track_number: int
    score: float
    
    class Config:
        from_attributes = True

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

class ReviewFull(ReviewSummary):
    review_text: Optional[str] = None
    tracks: List[TrackSchema] = []

class CalendarResponse(BaseModel):
    month: int
    year: int
    days: Dict[str, List[ReviewSummary]]