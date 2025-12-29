from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class TrackBase(BaseModel):
    id: str
    name: str
    track_number: int
    duration_ms: int
    preview_url: Optional[str] = None

class AlbumBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    artist: str
    cover_url: Optional[str] = None
    release_date: Optional[str] = None

class AlbumFull(AlbumBase):
    total_tracks: int
    label: Optional[str] = None
    tracks: List[TrackBase] = []