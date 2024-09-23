from pydantic import BaseModel


class User(BaseModel):
    id: int
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    password: str


class Post(BaseModel):
    id: int
    content: str
    user_id: int
