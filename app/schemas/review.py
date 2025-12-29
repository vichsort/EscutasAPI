from pydantic import BaseModel, Field, ConfigDict, UUID4
from typing import List, Optional
from datetime import datetime

class TrackInput(BaseModel):
    id: Optional[str] = None  
    name: str
    track_number: int
    userScore: float = Field(..., ge=0, le=10, description="Nota de 0 a 10")

class AlbumInput(BaseModel):
    id: Optional[str] = None 
    name: str
    artist: str
    cover: Optional[str] = None

class ReviewCreate(BaseModel):
    album: AlbumInput
    review_text: Optional[str] = None
    tracks: List[TrackInput]

class TrackOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID4
    name: str = Field(validation_alias='track_name') 
    track_number: int
    score: float

class ReviewSummary(BaseModel):
    """Schema leve para listagens"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    album_name: str
    artist_name: str
    cover: Optional[str] = Field(None, validation_alias='cover_url')
    spotify_album_id: str
    review_text: Optional[str] = None
    average_score: float
    tier: str
    created_at: datetime

class ReviewFull(BaseModel):
    """Schema completo para detalhes"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    album_name: str
    artist_name: str
    cover: Optional[str] = Field(None, validation_alias='cover_url')
    spotify_album_id: str
    review_text: Optional[str] = None
    average_score: float
    tier: str
    created_at: datetime 
    tracks: List[TrackOutput]