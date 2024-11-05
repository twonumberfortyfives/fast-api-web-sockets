from typing import Union

from fastapi import Depends, Request, APIRouter, Response, UploadFile
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_db
from posts import serializers, views
from fastapi_pagination import Page, paginate


router = APIRouter()


@router.get(
    "/posts",
    # dependencies=[Depends(RateLimiter(times=120, seconds=60))]
)
async def get_all_posts(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> Page[serializers.PostList]:
    return paginate(
        await views.get_all_posts_view(request=request, response=response, db=db)
    )


@router.get(
    "/posts/{post}",
    # dependencies=[Depends(RateLimiter(times=120, seconds=60))]
)
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


@router.post(
    "/posts/{post_id}/like",
    response_model=serializers.Like,
    # dependencies=[Depends(RateLimiter(times=120, seconds=60))],
)
async def like_the_post(
    post_id: int,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    return await views.like_the_post_view(
        post_id=post_id, request=request, response=response, db=db
    )


@router.delete(
    "/posts/{post_id}/like",
    # dependencies=[Depends(RateLimiter(times=120, seconds=60))]
)
async def unlike_the_post(
    post_id: int,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    return await views.unlike_the_post_view(
        post_id=post_id, request=request, response=response, db=db
    )


@router.post(
    "/posts",
    response_model=serializers.Post,
    # dependencies=[Depends(RateLimiter(times=120, seconds=60))],
)
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


@router.patch(
    "/posts/{post_id}",
    response_model=serializers.PostPatch,
    # dependencies=[Depends(RateLimiter(times=120, seconds=60))],
)
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


@router.post("/admin-make-posts")
async def admin_create_posts(db: AsyncSession = Depends(get_db)):
    await views.create_posts_as_admin(db=db)
    return {"message": "Posts created successfully"}
