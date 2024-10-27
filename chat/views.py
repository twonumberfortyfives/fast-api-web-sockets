import base64

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from fastapi import Request, Response
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import selectinload

from chat import serializers
from db import models
from dependencies import get_current_user, encrypt_message


async def get_chat_history(
    user_id: int, request: Request, response: Response, db: AsyncSession
):
    current_user = await get_current_user(request=request, response=response, db=db)
    query_receiver = await db.execute(
        select(models.DBUser)
        .filter(models.DBUser.id == user_id)
    )
    receiver = query_receiver.scalars().first()

    if receiver:
        result = await db.execute(
            select(models.DBMessage)
            .join(
                models.DBUser,
                models.DBUser.id == models.DBMessage.sender_id,
            )
            .options(selectinload(models.DBMessage.sender))
            .filter(models.DBMessage.sender_id == current_user.id)
            .filter(models.DBMessage.receiver_id == receiver.id)
            .order_by(models.DBMessage.created_at)
        )

        all_messages = result.scalars().all()

        if all_messages:
            return all_messages

    raise HTTPException(status_code=400, detail="No chat/user found.")


async def get_all_chats(request: Request, response: Response, db: AsyncSession):
    current_user_id = (
        await get_current_user(request=request, response=response, db=db)
    ).id

    query = await db.execute(
        select(models.DBConversation)
        .outerjoin(
            models.DBConversationMember,
            models.DBConversationMember.conversation_id == models.DBConversation.id,
        )
        .outerjoin(
            models.DBUser,
            models.DBConversationMember.user_id == models.DBUser.id,
        )
        .options(
            selectinload(models.DBConversation.members).selectinload(models.DBConversationMember.user)
        )
        .filter(models.DBConversationMember.user_id == current_user_id)
        .distinct()
    )

    result = query.scalars().all()

    all_chats = [
        {
            "id": chat.id,
            "name": chat.name,
            "username": next(member.user.username for member in chat.members if member.user.id != current_user_id),
            "profile_picture": next(member.user.profile_picture for member in chat.members if member.user.id != current_user_id),
            "created_at": chat.created_at,
        }
        for chat in result
    ]

    if all_chats:
        return all_chats
    raise HTTPException(status_code=400, detail="No chats found.")


async def delete_chat(
    chat_id: int, request: Request, response: Response, db: AsyncSession
):
    current_user = await get_current_user(request=request, response=response, db=db)
    query = await db.execute(
        select(models.DBConversation)
        .outerjoin(
            models.DBConversationMember,
            models.DBConversationMember.conversation_id == models.DBConversation.id,
        )
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
    current_user = await get_current_user(request=request, response=response, db=db)

    query_receiver = await db.execute(
        select(models.DBUser)
        .filter(models.DBUser.id == user_id)
    )
    receiver = query_receiver.scalars().first()
    if receiver:
        encrypted_message = await encrypt_message(message.content)
        encoded_data = base64.b64encode(encrypted_message).decode("utf-8")

        query = await db.execute(
            select(models.DBConversation)
            .join(
                models.DBConversationMember,
                models.DBConversationMember.conversation_id == models.DBConversation.id,
            )
            .options(selectinload(models.DBConversation.members))
            .where(models.DBConversationMember.user_id == current_user.id)
        )
        my_conversations = query.scalars().all()

        conversation = next(
            (
                conv
                for conv in my_conversations
                if any(member.user_id == user_id for member in conv.members)
            ),
            None,
        )

        if conversation is None:
            new_conversation = models.DBConversation(name="New Chat")
            db.add(new_conversation)
            await db.commit()
            await db.refresh(new_conversation)

            member1 = models.DBConversationMember(
                user_id=current_user.id, conversation_id=new_conversation.id
            )
            member2 = models.DBConversationMember(
                user_id=user_id, conversation_id=new_conversation.id
            )
            db.add_all([member1, member2])
            await db.commit()

            new_message = models.DBMessage(
                sender_id=current_user.id,
                receiver_id=user_id,
                conversation_id=new_conversation.id,
                content=encoded_data,
            )
            db.add(new_message)
            await db.commit()
            await db.refresh(new_message)

            return {"message": "Message has been sent and chat created."}

        new_message = models.DBMessage(
            sender_id=current_user.id,
            receiver_id=user_id,
            conversation_id=conversation.id,
            content=encoded_data,
        )
        db.add(new_message)
        await db.commit()
        await db.refresh(new_message)

        return {"message": "Message has been sent in existing chat."}
    raise HTTPException(detail="User not found", status_code=400)
