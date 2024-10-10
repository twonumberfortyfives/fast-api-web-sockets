from datetime import datetime, timezone

from pydantic import BaseModel, Field


class CommentList(BaseModel):
    id: int
    user_id: int
    post_id: int
    content: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        }
