from fastapi import Depends, Request, APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_db
from posts import serializers, views


router = APIRouter()


@router.get("/get-posts", response_model=list[serializers.PostList])
async def get_all_posts(db: AsyncSession = Depends(get_db)):
    return await views.get_all_posts_view(db)


@router.get("/get-posts/{post_id}", response_model=serializers.PostList)
async def retrieve_post(post_id: int, db: AsyncSession = Depends(get_db)):
    return await views.retrieve_post_view(post_id, db)


@router.post("/create-post", response_model=serializers.Post)
async def create_post(
    request: Request, post: serializers.PostCreate, db: AsyncSession = Depends(get_db)
):
    response = await views.create_post_view(db=db, request=request, post=post)
    return response


@router.patch("/edit-post/{post_id}", response_model=serializers.Post)
async def edit_post(
    post_update: serializers.PostUpdate,
    post_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await views.edit_post_view(
        post_update=post_update, post_id=post_id, request=request, db=db
    )

    return result


@router.delete("/delete-post/{post_id}")
async def delete_post(
    post_id: int, request: Request, db: AsyncSession = Depends(get_db)
):
    result = await views.delete_post_view(post_id=post_id, db=db, request=request)
    if result:
        return {"message": "Post deleted"}
    raise HTTPException(status_code=403, detail="Token validation error")
