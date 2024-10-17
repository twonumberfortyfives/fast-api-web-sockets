from sqlalchemy import (
    Integer,
    Column,
    String,
    ForeignKey,
    DateTime,
    Text,
    func,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship, validates
from db.engine import Base
from sqlalchemy.dialects.postgresql import ENUM
from enum import Enum as PyEnum


class Role(PyEnum):
    admin = "admin"
    user = "user"


class DBFile(Base):
    __tablename__ = 'files'
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    link = Column(String)
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'), nullable=False)

    post = relationship("DBPost", back_populates="files")


class DBUser(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    email = Column(String, unique=True, nullable=False)
    username = Column(String(30), unique=True, nullable=False)
    profile_picture = Column(
        String, default="http://127.0.0.1:8000/uploads/default.jpg"
    )
    password = Column(String, nullable=False)
    bio = Column(String(500), nullable=True)
    role = Column(ENUM(Role), nullable=False, default=Role.user)
    created_at = Column(DateTime, server_default=func.now())

    posts = relationship("DBPost", back_populates="user", cascade="all, delete-orphan")

    post_likes = relationship(
        "DBPostLike", back_populates="user", cascade="all, delete-orphan"
    )

    comments = relationship(
        "DBComment", back_populates="user", cascade="all, delete-orphan"
    )

    # received_messages = relationship("DBMessage", foreign_keys=["DBMessage.receiver_id"], back_populates="receiver")
    # sent_messages = relationship("DBMessage", foreign_keys=["DBMessage.sender_id"], back_populates="sender")


class DBPost(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    topic = Column(String(255), nullable=True)
    content = Column(String(500), nullable=False)
    files = relationship("DBFile", back_populates="post", cascade="all, delete-orphan")  # Relationship to files
    _tags = Column(String(500), nullable=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime, server_default=func.now())
    user = relationship("DBUser", back_populates="posts")

    likes = relationship(
        "DBPostLike",
        back_populates="post",
        cascade="all, delete-orphan",
    )
    comments = relationship(
        "DBComment",
        back_populates="post",
        cascade="all, delete-orphan",
    )

    @property
    def tags(self):
        return [tag.strip() for tag in self._tags.split(",")] if self._tags else []

    @tags.setter
    def tags(self, tags):
        if tags is not None:
            self._tags = ",".join(tag.strip() for tag in tags)

    @validates("topic", "content")
    def validate_topic(self, key, value):
        if value == "":
            raise ValueError("topic cannot be blank.")
        return value


# class DBMessage(Base):
#     __tablename__ = "messages"
#
#     id = Column(Integer, primary_key=True, autoincrement=True, index=True)
#     sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
#     receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
#     content = Column(String(500), nullable=False)
#     created_at = Column(DateTime, default=func.now())
#
#     sender = relationship("DBUser", foreign_keys=[sender_id], back_populates="sent_messages")
#     receiver = relationship("DBUser", foreign_keys=[receiver_id], back_populates="received_messages")


class DBPostLike(Base):
    __tablename__ = "post_likes"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)

    user = relationship("DBUser", back_populates="post_likes")
    post = relationship("DBPost", back_populates="likes")

    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="unique_user_post_like"),
        Index("idx_user_post", "user_id", "post_id"),
    )


class DBComment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    content = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=func.now())

    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)

    user = relationship("DBUser", back_populates="comments")
    post = relationship("DBPost", back_populates="comments")
    parent = relationship("DBComment", remote_side=[id], back_populates="replies")
    replies = relationship(
        "DBComment", back_populates="parent", cascade="all, delete-orphan"
    )

    @validates("content")
    def validate_content(self, key, value):
        if value == "":
            raise ValueError("topic cannot be blank.")
        return value
