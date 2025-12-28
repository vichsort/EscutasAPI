from pydantic import BaseModel, ConfigDict
from typing import Optional
from app.schemas.album import AlbumBase

class CurrentPlaybackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    is_playing: bool
    track_name: Optional[str] = None
    album: Optional[AlbumBase] = None

class SuggestionResponse(AlbumBase):
    reason: str