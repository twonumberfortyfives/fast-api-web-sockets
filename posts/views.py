from fastapi import HTTPException
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from dotenv import load_dotenv
import os

from db import models
from posts import serializers
from users.views import get_user_model

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


async def get_all_posts(db: AsyncSession):
    result = await db.execute(select(models.DBPost))
    posts = result.scalars().all()
    return posts


async def create_post(db: AsyncSession, access_token, post: serializers.PostCreate):
    if not access_token:
        raise HTTPException(status_code=403, detail="Not authorized")
    user_id = (await get_user_model(access_token=access_token, db=db)).id
    new_post = models.DBPost(
        topic=post.topic,
        content=post.content,
        created_at=post.created_at,
        user_id=user_id,
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    return new_post


async def change_post(
    post_update: serializers.PostUpdate,
    post_id: int,
    access_token: str,
    db: AsyncSession,
):
    user_id = (await get_user_model(access_token=access_token, db=db)).id
    result = await db.execute(select(models.DBPost).filter(models.DBPost.id == post_id))
    post = result.scalar_one_or_none()

    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.user_id != user_id:
        raise HTTPException(
            status_code=403, detail="You are not allowed to edit this post"
        )

    post.topic = post_update.topic
    post.content = post_update.content
    post.created_at = post_update.created_at

    db.add(post)
    await db.commit()
    await db.refresh(post)

    return post
