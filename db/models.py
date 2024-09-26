import datetime
from sqlalchemy import Integer, Column, String, ForeignKey, DateTime, Enum, Text, func
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
    created_at = Column(DateTime, server_default=func.now())

    posts = relationship("DBPost", back_populates="user", cascade="all, delete-orphan")
    sent_messages = relationship("DBMessage", foreign_keys="[DBMessage.sender_id]", back_populates="sender")

    # Removed received_messages to avoid confusion, as it's implicit in the chat structure
    participants = relationship("DBChatParticipant", back_populates="user")


class DBPost(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    topic = Column(String(255), nullable=True)
    content = Column(String(500), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    user = relationship("DBUser", back_populates="posts")


class DBChat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    chat_id = Column(String(64), unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    participants = relationship("DBChatParticipant", back_populates="chat")
    messages = relationship("DBMessage", back_populates="chat")


class DBChatParticipant(Base):
    __tablename__ = "chat_participants"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    added_at = Column(DateTime, server_default=func.now())

    chat = relationship("DBChat", back_populates="participants")
    user = relationship("DBUser", back_populates="participants")


class DBMessage(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    chat = relationship("DBChat", back_populates="messages")
    sender = relationship("DBUser", back_populates="sent_messages")

    # Removed receiver_id as it's not explicitly needed
