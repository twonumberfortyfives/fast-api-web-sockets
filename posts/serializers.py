from typing import Optional

from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
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


class Like(BaseModel):
    id: int
    user_id: int
    post_id: int


class PostList(BaseModel):
    id: int
    topic: str
    content: str
    tags: list[str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user: Optional[UserForPostList]
    likes_count: int = 0  # Add a field for counting likes
    comments_count: int = 0
    is_liked: bool = False

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        }

    @model_validator(mode="before")
    def count_all_likes_and_comments(cls, values):
        values.likes_count = len(values.likes)
        values.comments_count = len(values.comments)
        return values


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
