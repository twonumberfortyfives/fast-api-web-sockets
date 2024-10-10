from fastapi import HTTPException, Request, Response
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
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
        .outerjoin(models.DBPostLike)
        .options(selectinload(models.DBPost.likes))
        .order_by(models.DBPost.id.desc())
    )
    posts = result.scalars().all()
    if posts:
        return posts

    raise HTTPException(status_code=404, detail="No posts found")


async def retrieve_post_view(post, db: AsyncSession):
    if post.isdigit():
        post = int(post)
        result = await db.execute(
            select(models.DBPost)
            .outerjoin(models.DBUser)
            .options(selectinload(models.DBPost.user))
            .outerjoin(models.DBPostLike)
            .options(selectinload(models.DBPost.likes))
            .filter(models.DBPost.id == post)
            .order_by(models.DBPost.id.desc())  # Sort by ID in descending order
        )
        post = result.scalars().first()
        if post:
            return [post]

    if isinstance(post, str):
        result = await db.execute(
            select(models.DBPost)
            .outerjoin(models.DBUser)
            .options(selectinload(models.DBPost.user))
            .outerjoin(models.DBPostLike)
            .options(selectinload(models.DBPost.likes))
            .filter(models.DBPost.topic.ilike(f"%{post}%"))
            .order_by(models.DBPost.id.desc())  # Sort by ID in descending order
        )
        post = result.scalars().all()
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
        tags=post.tags,
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    return new_post


async def edit_post_view(
        post_id: int,
        request: Request,
        response: Response,
        db: AsyncSession,
        topic: str = None,
        content: str = None,
        tags: str = None,
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

    if tags:
        post.tags = [tags]
    if topic:
        post.topic = topic
    if content:
        post.content = content

    db.add(post)
    await db.commit()
    await db.refresh(post)

    return post


async def delete_post_view(
        db: AsyncSession, post_id: int, request: Request, response: Response
):
    is_deleted = False
    result = await db.execute(select(models.DBPost).filter(models.DBPost.id == post_id))
    post = result.scalar_one_or_none()
    if post:
        user = (await get_current_user(request=request, db=db, response=response)).id
        if post.user_id == user:
            await db.delete(post)
            await db.commit()
            is_deleted = True
        if is_deleted:
            return {"message": "Post deleted"}
        raise HTTPException(
            status_code=403, detail="You are not allowed to delete this post"
        )
    else:
        raise HTTPException(status_code=404, detail="No post found")


async def like_the_post_view(post_id: int, request: Request, response: Response, db: AsyncSession):
    current_user_id = (await get_current_user(request=request, response=response, db=db)).id
    try:
        new_like = models.DBPostLike(
            user_id=current_user_id,
            post_id=post_id,
        )
        db.add(new_like)
        await db.commit()
        await db.refresh(new_like)
        return new_like
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="You already liked this post or post does not exist")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


async def unlike_the_post_view(post_id: int, request: Request, response: Response, db: AsyncSession):
    current_user_id = (await get_current_user(request=request, response=response, db=db)).id
    result = await db.execute(
        select(models.DBPostLike)
        .filter(models.DBPostLike.user_id == current_user_id)
        .filter(models.DBPostLike.post_id == post_id)

    )
    like_found = result.scalar_one_or_none()
    if like_found:
        await db.delete(like_found)
        await db.commit()
        return {"message": "Post unliked"}
    raise HTTPException(status_code=404, detail="Like not found")
