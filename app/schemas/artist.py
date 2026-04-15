from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class ArtistSummary(BaseModel):
    id: str
    name: str
    image_url: Optional[str] = None

class PlatinumStats(BaseModel):
    total_required: int
    completed_count: int
    percentage: int
    is_platinum: bool

class DiscographyItem(BaseModel):
    clean_name: str
    cover_url: Optional[str] = None
    release_date: str
    is_completed: bool

class PlatinumProgressOutput(BaseModel):
    """Schema principal de resposta para o progresso da platina"""
    artist: ArtistSummary
    stats: PlatinumStats
    discography: List[DiscographyItem]

class PlatinumTrophyOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    spotify_artist_id: str
    artist_name: str
    artist_image_url: Optional[str] = None
    achieved_at: datetime