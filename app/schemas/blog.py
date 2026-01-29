from pydantic import BaseModel, Field, ConfigDict, UUID4, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
import re

class TrackSnapshot(BaseModel):
    """O que guardamos de cada música no banco para não chamar o Spotify na leitura"""
    name: str
    artist: str
    album: str
    cover_url: Optional[str] = None
    preview_url: Optional[str] = None

class PostCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=255)
    slug: str = Field(..., min_length=5, max_length=255)
    summary: Optional[str] = Field(None, max_length=500)
    content: str
    cover_image: Optional[str] = Field(None, alias='cover_image_url')
    related_review_id: Optional[UUID4] = None
    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not re.match(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', v):
            raise ValueError('O slug deve conter apenas letras minúsculas, números e hífens (ex: meu-post-legal)')
        return v

class PostUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    cover_image: Optional[str] = Field(None, alias='cover_image_url')
    status: Optional[str] = None
    related_review_id: Optional[UUID4] = None

class AuthorSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    display_name: str
    avatar_url: Optional[str] = None

class BlogPostList(BaseModel):
    """Versão resumida para listagens (Cards do Blog)"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID4
    title: str
    slug: str
    summary: Optional[str] = None
    cover_image_url: Optional[str] = None
    published_at: Optional[datetime] = None
    author: AuthorSummary

class BlogPostDetail(BaseModel):
    """Versão completa para a página do Post"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID4
    title: str
    slug: str
    content: str
    cover_image_url: Optional[str] = None
    track_metadata: Dict[str, TrackSnapshot] = Field(default_factory=dict)
    
    status: str
    created_at: datetime
    published_at: Optional[datetime] = None
    
    author: AuthorSummary
    related_review_id: Optional[UUID4] = None