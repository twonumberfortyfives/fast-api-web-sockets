import json
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, Request, Response
from passlib.context import CryptContext
import aioredis
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


async def get_total_posts_in_db(db: AsyncSession):
    all_posts = await db.execute(select(models.DBPost))
    return all_posts.scalars().all()


def serialize(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


async def cache_all_posts(redis_client, posts: list[models.DBPost]):
    # Serialize and store each post individually in Redis
    for post in posts:
        serialized_post = json.dumps(
            serializers.PostList.from_orm(post).dict(), default=serialize
        )
        await redis_client.rpush("all_posts", serialized_post)

    # Set an expiration time for the key
    await redis_client.expire("all_posts", 60)  # Cache for 60 seconds


async def get_all_posts_from_db(db: AsyncSession, offset: int, page_size: int):
    # Execute a query to select posts with pagination
    result = await db.execute(
        select(models.DBPost)
        .outerjoin(models.DBUser)
        .options(selectinload(models.DBPost.user))
        .order_by(models.DBPost.id.desc())  # Sort by ID in descending order
        .offset(offset)  # Apply the offset
        .limit(page_size)  # Apply the limit for pagination
    )
    posts = result.scalars().all()  # Get all posts from the result
    return posts


async def get_all_posts_without_pagination(db: AsyncSession):
    result = await db.execute(
        select(models.DBPost)
        .outerjoin(models.DBUser)
        .options(selectinload(models.DBPost.user))
        .order_by(models.DBPost.id.desc())  # Sort by ID in descending order
    )
    posts = result.scalars().all()
    return posts


async def get_all_posts_from_cache(
    redis_client, offset: int, page_size: int
) -> Optional[list[dict]]:
    cached_posts = await redis_client.lrange(
        "all_posts", offset, offset + page_size - 1
    )

    if cached_posts:
        return [json.loads(post) for post in cached_posts]

    return []


async def get_all_posts_view(page: int, page_size: int, db: AsyncSession):
    redis_client = aioredis.from_url("redis://redis:6379/0")

    offset = (page - 1) * page_size

    cached_posts = await get_all_posts_from_cache(redis_client, offset, page_size)

    if cached_posts:
        print("Posts received from cache")
        return cached_posts

    posts = await get_all_posts_from_db(db, offset, page_size)

    if posts:
        await cache_all_posts(redis_client, posts)  # Cache the posts
        print("Posts received from db and cached")
        return posts

    raise HTTPException(status_code=404, detail="No posts found")


async def retrieve_post_view(post, page, page_size, db: AsyncSession):
    if post.isdigit():
        post = int(post)
        result = await db.execute(
            select(models.DBPost)
            .outerjoin(models.DBUser)
            .options(selectinload(models.DBPost.user))
            .filter(models.DBPost.id == post)
            .order_by(models.DBPost.id.desc())  # Sort by ID in descending order
        )
        post = result.scalar_one_or_none()

    if isinstance(post, str):
        if page and page_size:
            offset = (page - 1) * page_size
            result = await db.execute(
                select(models.DBPost)
                .outerjoin(models.DBUser)
                .options(selectinload(models.DBPost.user))
                .filter(models.DBPost.topic.ilike(f"%{post}%"))
                .order_by(models.DBPost.id.desc())  # Sort by ID in descending order
                .offset(offset)  # Apply the offset
                .limit(page_size)
            )
            post = result.scalars().all()
        else:
            raise HTTPException(
                status_code=400,
                detail="Searching by post's topic must be with page and page size!",
            )
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
