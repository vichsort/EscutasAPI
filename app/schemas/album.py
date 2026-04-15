from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class TrackBase(BaseModel):
    id: str
    name: str
    track_number: int
    duration_ms: int
    preview_url: Optional[str] = None
    suggested_ignore: bool = False

class AlbumBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    clean_name: Optional[str] = None 
    artist: str
    cover_url: Optional[str] = None
    release_date: Optional[str] = None
    is_canonical: bool = True 

class AlbumFull(AlbumBase):
    total_tracks: int
    tracks: List[TrackBase] = []