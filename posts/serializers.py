from typing import Optional

from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import datetime, timezone


class Post(BaseModel):
    id: int
    topic: str
    content: str
    tags: list[str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: int

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        }


class UserForPostList(BaseModel):
    id: int
    username: str
    email: EmailStr
    profile_picture: str

    class Config:
        from_attributes = True


class PostList(BaseModel):
    id: int
    topic: str
    content: str
    tags: list[str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user: Optional[UserForPostList]

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        }


class PostCreate(BaseModel):
    topic: str
    content: str
    tags: list[str]

    @field_validator("topic")
    def validate_topic(cls, value):
        if not value.strip():
            raise ValueError("Topic cannot be empty.")
        return value

    @field_validator("content")
    def validate_content(cls, value):
        if not value.strip():
            raise ValueError("Topic cannot be empty.")
        return value


class PostUpdate(BaseModel):
    topic: str
    content: str
    tags: list[str]
