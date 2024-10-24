from datetime import datetime, timezone

from pydantic import BaseModel, Field, model_validator


class MessageCreate(BaseModel):
    sender_id: int
    receiver_id: int
    conversation_id: int
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        }


class Message(BaseModel):
    id: int
    user_id: int
    chat_id: int
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        }


class Participant(BaseModel):
    id: int
    email: str
    username: str


class Chat(BaseModel):
    id: int
    messages: list[Message] = []
    participants: list[Participant] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        }


class ChatList(BaseModel):
    id: int
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        }


class MessagesList(BaseModel):
    id: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    content: str
    username: str
    profile_picture: str

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        }

    @model_validator(mode="before")
    def count_all_likes_and_comments(cls, values):
        values.username = values.sender.username
        values.profile_picture = values.sender.profile_picture
        return values


class MessageAndChatCreate(BaseModel):
    content: str
