from pydantic import BaseModel, UUID4, Field
from typing import Optional

class UserPublic(BaseModel):
    uuid: UUID4 = Field(..., alias="id")
    spotify_id: str
    display_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserProfile(UserPublic):
    joined_at: Optional[str] = None