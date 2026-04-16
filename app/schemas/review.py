from pydantic import BaseModel, Field, ConfigDict, UUID4
from typing import List, Optional
from datetime import datetime

class TrackInput(BaseModel):
    id: Optional[str] = None
    name: str 
    track_number: int
    userScore: Optional[float] = Field(None, ge=0, le=10)
    is_ignored: bool = False

class AlbumInput(BaseModel):
    id: Optional[str] = None
    name: str
    artist: str
    cover: Optional[str] = None 

class ReviewCreate(BaseModel):
    album: AlbumInput
    review_text: Optional[str] = None
    listened_date: Optional[str] = None
    tracks: List[TrackInput]
    is_private: bool = False

class TrackOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID4
    track_name: str 
    track_number: int
    score: Optional[float] = None
    is_ignored: bool

class ReviewSummary(BaseModel):
    """Para listagens (Sidebar, Library)"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    user_id: UUID4 
    spotify_album_id: str
    album_name: str
    artist_name: str
    cover_url: Optional[str] = None 
    review_text: Optional[str] = None
    average_score: float
    tier: str
    created_at: datetime
    is_private: bool
    artist_genres: list = []

class ReviewFull(ReviewSummary):
    """Para visualização detalhada. Herda tudo acima e adiciona as faixas."""
    tracks: List[TrackOutput]