from pydantic import BaseModel, Field, UUID4, ConfigDict
from typing import Literal

TargetType = Literal['REVIEW', 'POST', 'COMMENT']

class CommentCreate(BaseModel):
    target_id: UUID4
    target_type: TargetType
    content: str = Field(..., min_length=1, max_length=1000, description="O corpo do comentário")

class VoteCreate(BaseModel):
    target_id: UUID4
    target_type: TargetType
    # 1 (Up) ou -1 (Down)
    value: Literal[1, -1]