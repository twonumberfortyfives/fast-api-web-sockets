from fastapi import Depends, Request, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_db
from posts import serializers, views

router = APIRouter()


@router.get("/get-posts", response_model=list[serializers.Post])
async def get_all_posts(db: AsyncSession = Depends(get_db)):
    return await views.get_all_posts(db)


@router.post("/create-post", response_model=serializers.Post)
async def create_post(
    request: Request, post: serializers.PostCreate, db: AsyncSession = Depends(get_db)
):
    access_token = request.cookies.get("access_token")
    response = await views.create_post(db=db, access_token=access_token, post=post)
    return response
