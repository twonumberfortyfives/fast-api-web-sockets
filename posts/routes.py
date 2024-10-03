from fastapi import Depends, Request, APIRouter, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies import get_db
from posts import serializers, views


router = APIRouter()


@router.get("/posts", response_model=list[serializers.PostList])
async def get_all_posts(db: AsyncSession = Depends(get_db)):
    return await views.get_all_posts_view(db)


@router.get(
    "/posts/{post}", response_model=list[serializers.PostList] | serializers.PostList
)
async def retrieve_post(post, db: AsyncSession = Depends(get_db)):
    return await views.retrieve_post_view(post, db)


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
    post_update: serializers.PostUpdate,
    post_id: int,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    return await views.edit_post_view(
        post_update=post_update,
        post_id=post_id,
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
