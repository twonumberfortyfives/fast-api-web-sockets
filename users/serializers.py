from datetime import datetime, timezone

from pydantic import BaseModel, EmailStr, constr, field_validator, Field, model_validator

from posts.serializers import Post


def validate_password(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not any(char.isdigit() for char in value):
        raise ValueError("Password must contain at least one digit")
    if not any(char.isupper() for char in value):
        raise ValueError("Password must contain at least one uppercase letter")
    if not any(char.islower() for char in value):
        raise ValueError("Password must contain at least one lowercase letter")
    return value


class UserCreate(BaseModel):
    email: EmailStr
    username: constr(min_length=3, max_length=20)
    password: str

    @field_validator("password")
    def check_password(cls, value):
        return validate_password(value)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshToken(BaseModel):
    refresh_token: str


class UserList(BaseModel):
    id: int
    email: EmailStr
    profile_picture: str
    username: str
    bio: str | None

    class Config:
        from_attributes = True


class PostsAuthor(BaseModel):
    id: int
    username: str
    email: EmailStr
    profile_picture: str


class UserPosts(BaseModel):
    id: int
    topic: str
    content: str
    tags: list[str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user: PostsAuthor
    likes_count: int = 0

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        }

    @model_validator(mode="before")
    def count_all_likes(cls, values):
        values.likes_count = len(values.likes)
        return values


class UserMyProfile(BaseModel):
    id: int
    email: EmailStr
    profile_picture: str
    username: str
    bio: str | None
    posts: list[Post]

    class Config:
        from_attributes = True


class UserPasswordEdit(BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    def validate_new_password(cls, value):
        return validate_password(value)


class UserDeleteAccountPasswordConfirm(BaseModel):
    password: str
