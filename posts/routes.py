from typing import Union

from fastapi import Depends, Request, APIRouter, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_db
from posts import serializers, views
from fastapi_pagination import Page, paginate


router = APIRouter()


@router.get("/posts")
async def get_all_posts(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> Page[serializers.PostList]:
    return paginate(
        await views.get_all_posts_view(request=request, response=response, db=db)
    )


@router.get("/posts/{post}")
async def retrieve_post(
    post: Union[int, str],
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> Page[serializers.PostList]:
    return paginate(
        await views.retrieve_post_view(
            post=post, request=request, response=response, db=db
        )
    )


@router.post("/posts/{post_id}/like", response_model=serializers.Like)
async def like_the_post(
    post_id: int,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    return await views.like_the_post_view(
        post_id=post_id, request=request, response=response, db=db
    )


@router.delete("/posts/{post_id}/like")
async def unlike_the_post(
    post_id: int,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    return await views.unlike_the_post_view(
        post_id=post_id, request=request, response=response, db=db
    )


@router.post("/posts", response_model=serializers.Post)
async def create_post(
    request: Request,
    response: Response,
    files: list[UploadFile] | list[str] = None,
    topic: str = None,
    content: str = None,
    tags: str = None,
    db: AsyncSession = Depends(get_db),
):
    return await views.create_post_view(
        db=db,
        request=request,
        topic=topic,
        content=content,
        tags=tags,
        files=files,
        response=response,
    )


@router.patch("/posts/{post_id}", response_model=serializers.PostPatch)
async def edit_post(
    post_id: int,
    request: Request,
    response: Response,
    topic: str = None,
    content: str = None,
    tags: str = None,
    db: AsyncSession = Depends(get_db),
):
    return await views.edit_post_view(
        post_id=post_id,
        topic=topic,
        content=content,
        tags=tags,
        request=request,
        db=db,
        response=response,
    )


@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: int,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    return await views.delete_post_view(
        post_id=post_id, db=db, request=request, response=response
    )
