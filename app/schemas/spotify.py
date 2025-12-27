from pydantic import BaseModel
from typing import Optional, List
from app.schemas.album import AlbumBase

class CurrentPlaybackResponse(BaseModel):
    is_playing: bool
    track_name: Optional[str] = None
    album: Optional[AlbumBase] = None
    
    class Config:
        from_attributes = True

class SuggestionResponse(AlbumBase):
    reason: str