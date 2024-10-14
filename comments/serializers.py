from datetime import datetime, timezone

from pydantic import BaseModel, Field, model_validator


class CommentList(BaseModel):
    id: int
    user_id: int
    username: str
    email: str
    profile_picture: str
    post_id: int
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        }

    @model_validator(mode="before")
    def get_users_values(cls, values):
        values.username = values.user.username
        values.email = values.user.email
        values.profile_picture = values.user.profile_picture
        return values


class CommentCreate(BaseModel):
    user_id: int
    username: str
    email: str
    profile_picture: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        }
