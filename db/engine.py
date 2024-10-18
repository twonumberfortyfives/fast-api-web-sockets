import os
import dotenv
from sqlalchemy import Table, Column, ForeignKey, Integer
from sqlmodel import SQLModel

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


dotenv.load_dotenv()


DATABASE_URL = os.getenv(
    "DATABASE_URL"
)  # change if connecting via IDE/docker container

engine = create_async_engine(DATABASE_URL, echo=True, future=True)
async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    async with engine.begin() as conn:
        # await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)


Base = declarative_base()


user_chat_table = Table(
    'user_chat',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('chat_id', Integer, ForeignKey('chats.id'), primary_key=True)
)