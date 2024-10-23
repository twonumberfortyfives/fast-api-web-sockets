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
    current_user_id = (
        await get_current_user(request=request, response=response, db=db)
    ).id
    result = await db.execute(
        select(models.DBConversation)
        .outerjoin(models.DBConversationMember, models.DBConversationMember.conversation_id == models.DBConversation.id)
        .outerjoin(models.DBMessage, models.DBMessage.conversation_id == models.DBConversation.id)
        .options(
            selectinload(models.DBConversation.members)
            .selectinload(models.DBConversationMember.user),  # Load members
            selectinload(models.DBConversation.messages)  # Load messages
            .selectinload(models.DBMessage.sender)  # Load message sender
        )
        .filter(models.DBConversation.id == chat_id)
        .filter(models.DBConversationMember.user_id == current_user_id)
        .order_by(models.DBConversation.created_at)
    )

    chat = result.scalars().first()

    if chat:
        return {
            "id": chat.id,
            "messages": [
                {
                    "id": message.id,
                    "sender_id": message.sender_id,
                    "username": message.sender.username,
                    "profile_picture": message.sender.profile_picture,  # Access profile picture
                    "content": message.content,
                    "created_at": message.created_at,
                }
                for message in chat.messages
            ],
            "created_at": chat.created_at,
            "members": [
                {
                    "id": member.user.id,
                    "username": member.user.username,
                    "email": member.user.email,
                    "profile_picture": member.user.profile_picture,
                }
                for member in chat.members
            ],
        }
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