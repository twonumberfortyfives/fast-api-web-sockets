from pydantic import BaseModel, Field, EmailStr, validator
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

    @validator("topic")
    def validate_topic(cls, value):
        if not value.strip():
            raise ValueError("Topic cannot be empty.")
        return value

    @validator("content")
    def validate_content(cls, value):
        if not value.strip():
            raise ValueError("Topic cannot be empty.")
        return value


class PostUpdate(BaseModel):
    topic: str
    content: str
