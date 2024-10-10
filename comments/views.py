from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db import models


async def get_all_comments_view(db: AsyncSession):
    result = await db.execute(
        select(models.DBComment)
    )
    comments = result.scalars().all()
    return comments
