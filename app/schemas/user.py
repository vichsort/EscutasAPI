from pydantic import BaseModel, UUID4, Field, ConfigDict
from typing import Optional

class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 = Field(..., alias="id")
    spotify_id: str
    display_name: Optional[str] = None

class UserProfile(UserPublic):
    joined_at: Optional[str] = None