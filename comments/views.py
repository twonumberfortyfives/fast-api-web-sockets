from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import Response, Request
from fastapi.exceptions import HTTPException

from db import models
from dependencies import get_current_user


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


async def delete_comment(request: Request, response: Response, post_id: int, comment_id: int, db: AsyncSession):
    current_user_id = (await get_current_user(request=request, response=response, db=db)).id
    current_comment_payload = await db.execute(
        select(models.DBComment)
        .filter(models.DBComment.post_id == post_id)
        .filter(models.DBComment.id == comment_id)
        .filter(models.DBComment.user_id == current_user_id)
    )

    current_comment = current_comment_payload.scalars().first()

    if current_comment:
        await db.delete(current_comment)
        await db.commit()
        return {"message": "The comment has been deleted."}
    raise HTTPException(status_code=400, detail="An error has been occurred.")
