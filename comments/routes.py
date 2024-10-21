from fastapi import APIRouter, Depends, Request, Response
from fastapi_pagination import paginate, Page
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_db
from comments import views
from comments import serializers


router = APIRouter()


@router.get("/posts/{post_id}/all-comments/")
async def get_comments(
    post_id: int, db: AsyncSession = Depends(get_db)
) -> Page[serializers.CommentList]:
    return paginate(await views.get_all_comments_view(db=db, post_id=post_id))


@router.delete("/posts/{post_id}/all-comments/{comment_id}/")
async def delete_comment(
    post_id: int,
    comment_id: int,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    return await views.delete_comment(request=request, response=response, post_id=post_id, comment_id=comment_id, db=db)
