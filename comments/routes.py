from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_db
from comments import views


router = APIRouter()


@router.get("/hello")
async def root():
    return {"message": "Hello World"}


@router.get("/comments")
async def get_all_comments(db: AsyncSession = Depends(get_db)):
    return await views.get_all_comments_view(db=db)
