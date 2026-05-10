from pydantic import BaseModel, ConfigDict, field_validator
from typing import List, Optional
from datetime import datetime

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

class CurationVoteInput(BaseModel):
    is_canonical: bool

class CustomAlbumTrackCreate(BaseModel):
    name: str
    track_number: int
    duration_ms: Optional[int] = None

class CustomAlbumTrackOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    track_number: int
    duration_ms: Optional[int] = None

    @field_validator('id', mode='before')
    @classmethod
    def coerce_id(cls, v) -> str:
        return str(v)

class CustomAlbumCreate(BaseModel):
    name: str
    artist_name: str
    cover_url: Optional[str] = None
    tracks: List[CustomAlbumTrackCreate] = []

    @field_validator('cover_url')
    @classmethod
    def validate_cover_url(cls, v):
        if v and not v.startswith(('https://', 'http://')):
            raise ValueError('cover_url deve ser uma URL válida.')
        return v

class CustomAlbumOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    artist_name: str
    cover_url: Optional[str] = None
    created_at: datetime
    spotify_album_id: str
    tracks: List[CustomAlbumTrackOutput] = []

    @field_validator('id', mode='before')
    @classmethod
    def coerce_id(cls, v) -> str:
        return str(v)