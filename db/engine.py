import os
import dotenv
from sqlmodel import SQLModel

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


dotenv.load_dotenv()


USE_MOCK_DB = os.getenv("USE_MOCK_DB")

if USE_MOCK_DB == "true":
    DATABASE_URL = os.getenv(
        "MOCK_DATABASE_URL"
    )  # change if connecting via IDE/docker container
else:
    DATABASE_URL = os.getenv("DATABASE_URL")


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
