
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from fastapi import Request, Response
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import selectinload

from db import models
from dependencies import get_current_user


async def get_chat(chat_id: int, request: Request, response: Response, db: AsyncSession):
    current_user_id = (await get_current_user(request=request, response=response, db=db)).id
    result = await db.execute(
        select(models.DBConversation)
        .options(
            selectinload(models.DBConversation.members),
            selectinload(models.DBConversation.messages)
        )
        .distinct()
        .filter(models.DBConversation.id == chat_id)
        .order_by(models.DBConversation.created_at)
    )

    chat = result.scalars().first()
    if chat:
        return {
            "id": chat.id,
            "messages": [message for message in chat.messages],
            "created_at": chat.created_at,
            "members": [member for member in chat.members]
        }
    raise HTTPException(status_code=400, detail="No chats found.")


