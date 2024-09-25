from pydantic import BaseModel, Field
from datetime import datetime


class Post(BaseModel):
    id: int
    topic: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: int


class PostCreate(BaseModel):
    topic: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: int


class PostUpdate(BaseModel):
    topic: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
