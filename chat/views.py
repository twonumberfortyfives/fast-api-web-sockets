import uuid

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from fastapi import Request, Response
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import selectinload, aliased
from sqlalchemy.util import NoneType

from chat import serializers
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


async def delete_chat(chat_id: int, request: Request, response: Response, db: AsyncSession):
    current_user = await get_current_user(request=request, response=response, db=db)
    query = await db.execute(
        select(models.DBConversation)
        .outerjoin(models.DBConversationMember, models.DBConversationMember.conversation_id == models.DBConversation.id)
        .options(selectinload(models.DBConversation.members))
        .filter(models.DBConversationMember.user_id == current_user.id)
        .filter(models.DBConversation.id == chat_id)
        .distinct()
    )
    found_chat = query.scalars().first()

    if found_chat:
        await db.delete(found_chat)
        await db.commit()
        return {"message": "Chat has been deleted."}
    raise HTTPException(status_code=400, detail="No chats found.")


async def send_message_and_create_chat(
        request: Request,
        response: Response,
        message: serializers.MessageAndChatCreate,
        user_id: int,
        db: AsyncSession,
):
    current_user = await get_current_user(
        request=request,
        response=response,
        db=db
    )

    query = await db.execute(
        select(models.DBConversation)
        .join(models.DBConversationMember, models.DBConversation.id == models.DBConversationMember.conversation_id)
        .where(models.DBConversationMember.user_id.in_([current_user.id, user_id]))
        .group_by(models.DBConversation.id)
        .having(func.count(models.DBConversationMember.id) == 2)
    )
    conversation = query.scalars().first()

    if conversation is None:
        new_conversation = models.DBConversation(
            name=str(uuid.uuid4()),
        )
        db.add(new_conversation)
        await db.commit()
        await db.refresh(new_conversation)

        members = [
            models.DBConversationMember(user_id=current_user.id, conversation_id=new_conversation.id),
            models.DBConversationMember(user_id=user_id, conversation_id=new_conversation.id)
        ]
        db.add_all(members)
        await db.commit()
        await db.refresh(members)

        new_message = models.DBMessage(
            sender_id=current_user.id,
            receiver_id=user_id,
            conversation_id=new_conversation.id,
            content=message.content,
        )

        db.add(new_message)
        await db.commit()
        await db.refresh(new_message)

        return {"message": "Message has been sent and chat created."}

    new_message = models.DBMessage(
        sender_id=current_user.id,
        receiver_id=user_id,
        conversation_id=conversation.id,
        content=message.content,
    )

    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)

    return {"message": "Message has been sent in existing chat."}
