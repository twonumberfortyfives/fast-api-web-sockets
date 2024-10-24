from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from fastapi import Request, Response
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import selectinload

from db import models
from dependencies import get_current_user


async def get_chat_history(
    chat_id: int, request: Request, response: Response, db: AsyncSession
):
    current_user = (
        await get_current_user(request=request, response=response, db=db)
    )
    result = await db.execute(
        select(models.DBMessage)
        .join(models.DBConversation,
              models.DBMessage.conversation_id == models.DBConversation.id)
        .join(models.DBConversationMember,
              models.DBConversationMember.conversation_id == models.DBConversation.id)
        .options(selectinload(models.DBMessage.sender))
        .filter(models.DBConversation.id == chat_id)
        .filter(
            models.DBConversationMember.user_id == current_user.id)
        .order_by(models.DBMessage.created_at)
    )

    chat = result.scalars().all()

    if chat:
        return chat

    raise HTTPException(status_code=400, detail="No chats found.")


async def get_all_chats(request: Request, response: Response, db: AsyncSession):
    current_user_id = (await get_current_user(request=request, response=response, db=db)).id

    query = await db.execute(
        select(models.DBConversation)
        .outerjoin(models.DBConversationMember, models.DBConversationMember.conversation_id == models.DBConversation.id)
        .options(selectinload(models.DBConversation.members))
        .filter(models.DBConversationMember.user_id == current_user_id)
        .distinct()
    )

    all_chats = query.scalars().all()
    if all_chats:
        return all_chats
    raise HTTPException(status_code=400, detail="No chats found.")