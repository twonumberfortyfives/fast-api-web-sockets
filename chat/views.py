import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db import models


async def get_or_create_chat(sender_id: int, receiver_id: int, db: AsyncSession):
    result = await db.execute(
        select(models.DBChat)
        .join(models.DBChatParticipant)
        .filter(models.DBChatParticipant.user_id == sender_id)
        .filter(models.DBChatParticipant.chat_id == models.DBChat.id)
        .filter(models.DBChatParticipant.user_id == receiver_id)
    )

    chat = result.scalar_one_or_none()

    if chat:
        return chat
    else:
        # Create a new chat if it doesn't exist
        new_chat = models.DBChat(chat_id=str(uuid.uuid4()))
        db.add(new_chat)
        await db.commit()
        await db.refresh(new_chat)

        participant_1 = models.DBChatParticipant(chat_id=new_chat.id, user_id=sender_id)
        participant_2 = models.DBChatParticipant(chat_id=new_chat.id, user_id=receiver_id)

        db.add(participant_1)
        db.add(participant_2)
        await db.commit()
        await db.refresh(participant_1)
        await db.refresh(participant_2)

        return new_chat