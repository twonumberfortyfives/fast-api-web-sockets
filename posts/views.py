import random
import uuid
from typing import Optional

import httpx
from fastapi import HTTPException, Request, Response, UploadFile
from passlib.context import CryptContext
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from dotenv import load_dotenv
import os

from sqlalchemy.orm import selectinload

from db import models
import aiofiles
from dependencies import get_current_user, get_posts_with_full_info

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


async def get_all_posts_view(request: Request, response: Response, db: AsyncSession):
    result = await db.execute(
        select(models.DBPost)
        .outerjoin(models.DBUser, models.DBPost.user_id == models.DBUser.id)
        .options(selectinload(models.DBPost.user))
        .outerjoin(models.DBPostLike, models.DBPost.id == models.DBPostLike.post_id)
        .options(selectinload(models.DBPost.likes))
        .outerjoin(models.DBComment, models.DBPost.id == models.DBComment.post_id)
        .options(selectinload(models.DBPost.comments))
        .outerjoin(models.DBFile, models.DBPost.id == models.DBFile.post_id)
        .options(selectinload(models.DBPost.files))
        .distinct()
        .order_by(models.DBPost.id.desc())
    )
    posts = result.scalars().all()

    try:
        current_user_id = (
            await get_current_user(request=request, response=response, db=db)
        ).id
        if current_user_id:
            posts_with_full_info = await get_posts_with_full_info(
                posts=posts, current_user_id=current_user_id
            )
            return posts_with_full_info
        return posts
    except HTTPException as e:
        if e.status_code == 401:
            return posts
    raise HTTPException(status_code=404, detail="No posts found")


async def retrieve_post_view(
    post, request: Request, response: Response, db: AsyncSession
):
    query = (
        select(models.DBPost)
        .outerjoin(models.DBUser, models.DBPost.user_id == models.DBUser.id)
        .options(selectinload(models.DBPost.user))
        .outerjoin(models.DBPostLike, models.DBPost.id == models.DBPostLike.post_id)
        .options(selectinload(models.DBPost.likes))
        .outerjoin(models.DBComment, models.DBPost.id == models.DBComment.post_id)
        .options(selectinload(models.DBPost.comments))
        .outerjoin(models.DBFile, models.DBPost.id == models.DBFile.post_id)
        .options(selectinload(models.DBPost.files))
    )

    # Handle case when post is a digit (ID)
    if isinstance(post, str) and post.isdigit():
        post_id = int(post)
        result = await db.execute(
            query.filter(models.DBPost.id == post_id)
            .distinct()
            .order_by(models.DBPost.id.desc())
        )
        posts = result.scalars().all()

    elif isinstance(post, str):
        if post.startswith("#"):
            array_of_tags = post.split(",")
            without_hashtags = [tag.strip().lstrip("#") for tag in array_of_tags]

            conditions = [
                models.DBPost._tags.ilike(f"%{tag}%") for tag in without_hashtags
            ]
            result = await db.execute(
                query.filter(or_(*conditions))
                .distinct()
                .order_by(models.DBPost.id.desc())
            )
        else:
            result = await db.execute(
                query.filter(models.DBPost.topic.ilike(f"%{post}%"))
                .distinct()
                .order_by(models.DBPost.id.desc())
            )

        posts = result.scalars().all()

    else:
        raise HTTPException(status_code=404, detail="No post found")

    try:
        current_user_id = (
            await get_current_user(request=request, response=response, db=db)
        ).id
        return await get_posts_with_full_info(
            posts=posts, current_user_id=current_user_id
        )
    except HTTPException as e:
        if e.status_code == 401:
            return posts

    raise HTTPException(status_code=404, detail="No posts found")


async def create_post_view(
    db: AsyncSession,
    request: Request,
    response: Response,
    files: list[UploadFile] | None,
    topic: str,
    content: str,
    tags: Optional[str] = None,
):
    user_id = (await get_current_user(db=db, request=request, response=response)).id

    if not topic or not topic.strip():
        raise HTTPException(
            status_code=400, detail="Topic cannot be empty or contain only spaces."
        )

    if not content or not content.strip():
        raise HTTPException(
            status_code=400, detail="Content cannot be empty or contain only spaces."
        )

    if tags is not None and not tags.strip():
        raise HTTPException(
            status_code=400, detail="Tags cannot be empty or contain only spaces."
        )

    new_post = models.DBPost(
        topic=topic,
        content=content,
        user_id=user_id,
        _tags=tags,
    )

    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)

    if files and files != ["string"] and files != [""]:
        supported_types = ["image/png", "image/jpeg"]
        if any(file.content_type not in supported_types for file in files):
            raise HTTPException(status_code=400, detail="Picture type not supported.")

        os.makedirs("uploads", exist_ok=True)

        for file in files:
            image_path = f"uploads/{user_id}_{uuid.uuid4()}_{file.filename}"
            async with aiofiles.open(image_path, "wb") as f:
                await f.write(await file.read())

            file_record = models.DBFile(
                link=f"https://test.backendserviceforumapi.online/{image_path}",
                post_id=new_post.id,
            )
            db.add(file_record)
        await db.commit()

    query = (
        select(models.DBPost)
        .outerjoin(models.DBComment, models.DBPost.id == models.DBComment.post_id)
        .options(selectinload(models.DBPost.comments))
        .outerjoin(models.DBPostLike, models.DBPost.id == models.DBPostLike.post_id)
        .options(selectinload(models.DBPost.likes))
        .outerjoin(models.DBFile, models.DBPost.id == models.DBFile.post_id)
        .options(selectinload(models.DBPost.files))  # Ensure files are loaded
        .distinct()
        .where(models.DBPost.id == new_post.id)
    )

    result = await db.execute(query)
    return result.scalars().first()


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
    post = result.scalars().first()

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


async def like_the_post_view(
    post_id: int, request: Request, response: Response, db: AsyncSession
):
    current_user_id = (
        await get_current_user(request=request, response=response, db=db)
    ).id
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
        raise HTTPException(
            status_code=400, detail="You already liked this post or post does not exist"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


async def unlike_the_post_view(
    post_id: int, request: Request, response: Response, db: AsyncSession
):
    current_user_id = (
        await get_current_user(request=request, response=response, db=db)
    ).id
    result = await db.execute(
        select(models.DBPostLike)
        .filter(models.DBPostLike.user_id == current_user_id)
        .filter(models.DBPostLike.post_id == post_id)
        .distinct()
    )
    like_found = result.scalar_one_or_none()
    if like_found:
        await db.delete(like_found)
        await db.commit()
        return {"message": "Post unliked"}
    raise HTTPException(status_code=404, detail="Like not found")


async def get_all_posts_comments_view(post_id: int, db: AsyncSession):
    results = await db.execute(
        select(models.DBComment).filter(models.DBComment.post_id == post_id)
    )
    comments = results.scalars().all()
    return comments


async def fetch_data_news():
    random_page = random.randint(1, 100)
    url = f"https://newsapi.org/v2/everything?q=technology&pageSize=1&page={random_page}&apiKey={os.getenv('NEWS_API_KEY')}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        result = response.json()
    return [
        {
            "topic": article["title"],
            "content": article["description"],
            "picture": (article["urlToImage"] if article["urlToImage"] else None),
        }
        for article in result["articles"]
    ]


async def create_posts_as_admin(db: AsyncSession):
    admin_query = await db.execute(
        select(models.DBUser).filter(models.DBUser.username == "admin")
    )
    admin = admin_query.scalars().first()

    if not admin:
        new_admin = models.DBUser(
            email="admin@example.com",
            username="admin",
            password="rooT1234!",
        )
        db.add(new_admin)
        await db.commit()
        await db.refresh(new_admin)
        admin = new_admin

    fetched_data_news = await fetch_data_news()

    for news in fetched_data_news:
        new_post = models.DBPost(
            topic=news["topic"],
            content=news["content"],
            user_id=admin.id,
            _tags="admin, coding, programming",
        )
        db.add(new_post)
        await db.commit()
        await db.refresh(new_post)

        if news["picture"]:
            new_file_for_post = models.DBFile(post_id=new_post.id, link=news["picture"])
            db.add(new_file_for_post)
    await db.commit()
