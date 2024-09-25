import datetime

from sqlalchemy import Integer, Column, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from db.engine import Base


class Role(PyEnum):
    admin = "admin"
    user = "user"


class DBUser(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    email = Column(String, unique=True, nullable=False)
    username = Column(String(15), unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(Enum(Role), nullable=False, default=Role.user)

    posts = relationship("DBPost", back_populates="user", cascade="all, delete-orphan")


class DBPost(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    topic = Column(String(255), nullable=True)
    content = Column(String(500), nullable=False)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship("DBUser", back_populates="posts")
