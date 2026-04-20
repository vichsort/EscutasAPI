from pydantic import BaseModel, Field, ConfigDict, UUID4, field_validator
from typing import Optional, List, Literal
from datetime import datetime
import re

TargetType = Literal['REVIEW', 'ARTIST', 'ALBUM', 'TRACK']

class MentionBase(BaseModel):
    target_type: TargetType
    target_id: str
    target_name: Optional[str] = None

class MentionResponse(MentionBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4

class PostCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=255)
    content: str
    summary: Optional[str] = Field(None, max_length=500)
    cover_image_url: Optional[str] = None
    slug: Optional[str] = Field(None, min_length=5, max_length=255)
    mentions: List[MentionBase] = Field(default_factory=list)

    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', v):
            raise ValueError('O slug deve conter apenas letras minúsculas, números e hífens')
        return v

class PostUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    cover_image_url: Optional[str] = None
    status: Optional[str] = None
    mentions: Optional[List[MentionBase]] = None

class AuthorSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    display_name: str
    avatar_url: Optional[str] = None

class BlogPostList(BaseModel):
    """Card resumido para a listagem (Feed)"""
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    title: str
    slug: str
    summary: Optional[str] = None
    cover_image_url: Optional[str] = None
    published_at: Optional[datetime] = None
    author: AuthorSummary

class BlogPostDetail(BaseModel):
    """Página completa do Post"""
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    title: str
    slug: str
    content: str
    cover_image_url: Optional[str] = None
    status: str
    created_at: datetime
    published_at: Optional[datetime] = None
    author: AuthorSummary
    mentions: List[MentionResponse] = Field(default_factory=list)

class PaginatedBlogPostResponse(BaseModel):
    """Fronteira de Paginação Pydantic"""
    items: List[BlogPostList]
    total: int
    page: int
    pages: int