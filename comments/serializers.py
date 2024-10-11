from datetime import datetime, timezone

from pydantic import BaseModel, Field


class CommentList(BaseModel):
    id: int | None = None
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
