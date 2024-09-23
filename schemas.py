from pydantic import BaseModel, EmailStr, validator, Field
from datetime import datetime
from enum import Enum as PyEnum


class User(BaseModel):
    id: int
    email: EmailStr
    username: str
    password: str


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

    @validator("password")
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isupper() for char in value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in value):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char in "!@#$%^&*()_+-=" for char in value):
            raise ValueError(
                "Password must contain at least one special character (!@#$%^&*()_+-=)"
            )
        return value


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshToken(BaseModel):
    refresh_token: str


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


class UserList(BaseModel):
    id: int
    email: EmailStr
    username: str
    posts: list[Post] = []
