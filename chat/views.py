
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from fastapi import Request, Response
from sqlalchemy.orm import selectinload

from db import models
from dependencies import get_current_user


async def get_chat(chat_id: int, request: Request, response: Response, db: AsyncSession):
    current_user_id = (await get_current_user(request=request, response=response, db=db)).id
    result = await db.execute(
        select(models.DBChat)
        .options(
            selectinload(models.DBChat.messages),
        )
        .distinct()
        .filter(models.DBChat.id == chat_id)
        .order_by(models.DBChat.created_at)
    )

    chat = result.scalars().first()  # Get the first (and should be the only) chat
    return [
        {
            "id": message.id,
            "content": message.content,
            "created_at": message.created_at,
            "user_id": message.user_id,
        }
        for message in chat.messages
    ]

