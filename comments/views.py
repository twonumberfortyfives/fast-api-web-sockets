from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from db import models


async def get_all_comments_view(db: AsyncSession, post_id: int):
    comments_query = await db.execute(
        select(models.DBComment)
        .outerjoin(models.DBUser, models.DBComment.user_id == models.DBUser.id)
        .options(selectinload(models.DBComment.user))
        .filter(models.DBComment.post_id == post_id)
        .distinct()
        .order_by(models.DBComment.created_at)
    )
    comments = comments_query.scalars().all()
    return comments
