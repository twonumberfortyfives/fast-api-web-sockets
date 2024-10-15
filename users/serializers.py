from pydantic import BaseModel, EmailStr, constr, field_validator

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


class UserMyProfile(BaseModel):
    id: int
    email: EmailStr
    profile_picture: str
    username: str
    bio: str | None

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
