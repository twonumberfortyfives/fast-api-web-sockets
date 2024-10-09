from fastapi import Depends, Request, APIRouter, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies import get_db
from posts import serializers, views


router = APIRouter()


@router.get("/posts", response_model=list[serializers.PostList])
async def get_all_posts(response: Response, page: int = None, page_size: int = None, db: AsyncSession = Depends(get_db)):

    if page and page_size:
        all_posts = await views.get_all_posts_view(page, page_size, db)
        response.headers["X-all-posts-count"] = f"{len(all_posts)}"
        return await views.get_all_posts_view(page, page_size, db)
    else:
        all_posts = await views.get_all_posts_without_pagination(db)
        response.headers["X-all-posts-count"] = f"{len(all_posts)}"
        return all_posts


@router.get(
    "/posts/{post}", response_model=list[serializers.PostList] | serializers.PostList
)
async def retrieve_post(post, response: Response, page: int = None, page_size: int = None, db: AsyncSession = Depends(get_db)):
    if page and page_size:
        all_posts = await views.retrieve_post_view(post=post, page=page, page_size=page_size, db=db)
        response.headers["X-all-posts-count"] = f"{len(all_posts)}"
        return all_posts
    else:
        all_posts = await views.retrieve_post_view(post=post, page=page, page_size=page_size, db=db)
        return all_posts


@router.post("/posts", response_model=serializers.Post)
async def create_post(
    request: Request,
    response: Response,
    post: serializers.PostCreate,
    db: AsyncSession = Depends(get_db),
):
    return await views.create_post_view(
        db=db, request=request, post=post, response=response
    )


@router.patch("/posts/{post_id}", response_model=serializers.Post)
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
