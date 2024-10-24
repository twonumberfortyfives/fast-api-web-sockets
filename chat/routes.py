from fastapi import APIRouter, Depends, Request, Response
from fastapi_pagination import Page, paginate
from sqlalchemy.ext.asyncio import AsyncSession

from chat import views
from chat import serializers
from dependencies import get_db

router = APIRouter()


@router.get("/chats/{chat_id}/")
async def get_all_messages(
    chat_id: int,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> Page[serializers.MessagesList]:
    return paginate(await views.get_chat_history(
        chat_id=chat_id, request=request, response=response, db=db
    ))


@router.get("/chats")
async def get_all_chats(
        request: Request,
        response: Response,
        db: AsyncSession = Depends(get_db)
) -> Page[serializers.ChatList]:
    return paginate(await views.get_all_chats(request=request, response=response, db=db))


@router.delete("/chats/{chat_id}")
async def delete_chat(
        request: Request,
        response: Response,
        chat_id: int,
        db: AsyncSession = Depends(get_db),
):
    return await views.delete_chat(chat_id=chat_id, request=request, response=response, db=db)
