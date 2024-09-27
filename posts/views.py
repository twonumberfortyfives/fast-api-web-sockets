from fastapi import HTTPException, Request, Response
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from dotenv import load_dotenv
import os

from sqlalchemy.orm import selectinload

from db import models
from posts import serializers
from dependencies import get_current_user

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


async def get_all_posts_view(db: AsyncSession):
    result = await db.execute(
        select(models.DBPost)
        .outerjoin(models.DBUser)
        .options(selectinload(models.DBPost.user))
    )
    posts = result.scalars().all()
    if posts:
        return posts
    raise HTTPException(status_code=404, detail="No posts found")


async def retrieve_post_view(post, db: AsyncSession):
    result = None
    if post.isdigit():
        post = int(post)
        result = await db.execute(
            select(models.DBPost)
            .outerjoin(models.DBUser)
            .options(selectinload(models.DBPost.user))
            .filter(models.DBPost.id == post)
        )
    if isinstance(post, str):
        result = await db.execute(
            select(models.DBPost)
            .outerjoin(models.DBUser)
            .options(selectinload(models.DBPost.user))
            .filter(models.DBPost.topic.ilike(f"%{post}%"))
        )
    post = result.scalar_one_or_none()
    if post:
        return post
    else:
        raise HTTPException(status_code=404, detail="No post found")


async def create_post_view(
    db: AsyncSession, request: Request, response: Response, post: serializers.PostCreate
):
    user_id = (await get_current_user(db=db, request=request, response=response)).id
    new_post = models.DBPost(
        topic=post.topic,
        content=post.content,
        user_id=user_id,
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    return new_post


async def edit_post_view(
    post_update: serializers.PostUpdate,
    post_id: int,
    request: Request,
    response: Response,
    db: AsyncSession,
):
    user_id = (await get_current_user(request=request, db=db, response=response)).id
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

    db.add(post)
    await db.commit()
    await db.refresh(post)

    return post


async def delete_post_view(db: AsyncSession, post_id: int, request: Request, response: Response):
    result = await db.execute(select(models.DBPost).filter(models.DBPost.id == post_id))
    post = result.scalar_one_or_none()
    user = (await get_current_user(request=request, db=db, response=response)).id
    if post.user_id == user:
        await db.delete(post)
        await db.commit()
        return True
    raise HTTPException(
        status_code=403, detail="You are not allowed to delete this post"
    )
