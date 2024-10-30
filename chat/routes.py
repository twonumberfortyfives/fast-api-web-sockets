from fastapi import APIRouter, Depends, Request, Response
from fastapi_limiter.depends import RateLimiter
from fastapi_pagination import Page, paginate
from sqlalchemy.ext.asyncio import AsyncSession

from chat import views
from chat import serializers
from dependencies import get_db

router = APIRouter()


@router.get(
    "/chats/{user_id}",
    dependencies=[Depends(RateLimiter(times=30, seconds=60))],
)
async def get_all_messages(
    user_id: int,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> Page[serializers.MessagesList]:
    return paginate(
        await views.get_chat_history(
            user_id=user_id, request=request, response=response, db=db
        )
    )


@router.get(
    "/chats",
    dependencies=[Depends(RateLimiter(times=30, seconds=60))],
)
async def get_all_chats(
    request: Request, response: Response, db: AsyncSession = Depends(get_db)
) -> Page[serializers.ChatList]:
    return paginate(
        await views.get_all_chats(request=request, response=response, db=db)
    )


@router.delete(
    "/chats/{chat_id}",
    dependencies=[Depends(RateLimiter(times=30, seconds=60))],
)
async def delete_chat(
    request: Request,
    response: Response,
    chat_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await views.delete_chat(
        chat_id=chat_id, request=request, response=response, db=db
    )


@router.post(
    "/chats/{user_id}/send-message",
    response_model=serializers.MessagesList,
    dependencies=[Depends(RateLimiter(times=30, seconds=60))],
)
async def send_message_and_create_chat(
    request: Request,
    response: Response,
    message: serializers.MessageAndChatCreate,
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await views.send_message_and_create_chat(
        request=request,
        response=response,
        message=message,
        user_id=user_id,
        db=db,
    )


@router.delete(
    "/chats/{message_id}/delete-message",
    dependencies=[Depends(RateLimiter(times=30, seconds=60))],
)
async def delete_message(
    message_id: int,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    return await views.delete_message_view(
        message_id=message_id, request=request, response=response, db=db
    )


@router.patch(
    "/chats/{message_id}/edit-message",
    response_model=serializers.MessagesList,
    dependencies=[Depends(RateLimiter(times=30, seconds=60))],
)
async def patch_message(
    message_id: int,
    content: str,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    return await views.edit_message_view(
        message_id=message_id,
        content=content,
        request=request,
        response=response,
        db=db,
    )
