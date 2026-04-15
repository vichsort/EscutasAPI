from pydantic import BaseModel, UUID4, Field, ConfigDict
from typing import Optional, Dict, List

class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 = Field(..., alias="id")
    spotify_id: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None

class UserProfile(UserPublic):
    joined_at: Optional[str] = None
    review_count: int = 0
    platinum_count: int = 0
    blog_post_count: int = 0
    current_streak: int = 0

class StatsOverview(BaseModel):
    total_reviews: int
    total_platinums: int
    average_score: float

class TopArtistStat(BaseModel):
    name: str
    count: int

class UserStatsOutput(BaseModel):
    """Schema para renderizar os gráficos do perfil do usuário"""
    overview: StatsOverview
    tier_distribution: Dict[str, int]  # Ex: {"S": 10, "A": 5}
    top_artists: List[TopArtistStat]