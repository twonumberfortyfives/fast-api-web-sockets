from pydantic import BaseModel, Field, EmailStr
from datetime import datetime


class Post(BaseModel):
    id: int
    topic: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: int


class UserForPostList(BaseModel):
    id: int
    username: str
    email: EmailStr


class PostList(BaseModel):
    id: int
    topic: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user: UserForPostList


class PostCreate(BaseModel):
    topic: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: int


class PostUpdate(BaseModel):
    topic: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
