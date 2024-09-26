from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from chat import serializers, views
from dependencies import get_db

router = APIRouter()


# @router.post("/send-message")
# async def send_message(request: Request, message: serializers.MessageCreate, db: AsyncSession = Depends(get_db)):
#     return await views.send_message_view(request=request, message=message, db=db)
