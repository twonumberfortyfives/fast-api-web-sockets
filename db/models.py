import datetime

from sqlalchemy import Integer, Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from db.engine import Base


class DBUser(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    email = Column(String, unique=True, nullable=False)
    username = Column(String(255), unique=True, nullable=False)
    password = Column(String, nullable=False)

    posts = relationship("DBPost", back_populates="user")


class DBPost(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    topic = Column(String(255), nullable=True)
    content = Column(String(500), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship("DBUser", back_populates="posts")
