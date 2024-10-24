import os
import re

import aiohttp
import jwt
from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    Depends,

)
from fastapi.staticfiles import StaticFiles

from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import HTTPException
from sqlalchemy import func

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from chat.serializers import MessageCreate
from db import models
from db.engine import init_db
from dependencies import get_db
from users.routes import router as users_router
from posts.routes import router as posts_router
from chat.routes import router as chat_router
from comments.routes import router as comment_router
from comments.serializers import CommentCreate

app = FastAPI()
templates = Jinja2Templates(directory="templates")

add_pagination(app)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-all-posts-count"],
)

app.include_router(users_router, prefix="/api", tags=["users"])
app.include_router(posts_router, prefix="/api", tags=["posts"])
app.include_router(chat_router, prefix="/api", tags=["chat"])
app.include_router(comment_router, prefix="/api", tags=["comments"])

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.on_event("startup")
async def on_startup():
    await init_db()


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, dict[int, list[WebSocket]]] = {
            "chat": {},
            "post": {},
        }

    async def connect(self, websocket: WebSocket, group_name: int, group_type: str):
        await websocket.accept()
        if group_name not in self.active_connections[group_type]:
            self.active_connections[group_type][group_name] = []
        self.active_connections[group_type][group_name].append(websocket)

    def disconnect(self, websocket: WebSocket, group_name: int, group_type: str):
        self.active_connections[group_type][group_name].remove(websocket)
        if not self.active_connections[group_type][group_name]:
            del self.active_connections[group_type][group_name]

    async def broadcast(self, message: str, group_name: int, group_type: str):
        if group_name in self.active_connections[group_type]:
            for connection in self.active_connections[group_type][group_name]:
                await connection.send_text(message)


manager = ConnectionManager()


async def fetch(url, cookies):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, cookies=cookies) as response:
            if response.status == 200:
                return response
            else:
                return {"error": f"Failed to fetch data, status: {response.status}"}


@app.websocket("/ws/{post_id}")
async def websocket_comments(
    websocket: WebSocket, post_id: int, db: AsyncSession = Depends(get_db)
):
    await manager.connect(websocket, post_id, "post")
    while True:
        try:
            access_token = websocket.cookies.get("access_token")
            user_data = jwt.decode(
                access_token.encode("utf-8"),
                os.getenv("SECRET_KEY"),
                algorithms=[os.getenv("ALGORITHM")],
            )
            user_email = user_data.get("sub")

            current_user_payload = await db.execute(
                select(models.DBUser).filter(models.DBUser.email == user_email)
            )
            current_user = current_user_payload.scalars().first()

            data = await websocket.receive_json()

            if data:
                try:
                    comment_serializer = CommentCreate(
                        user_id=current_user.id,
                        username=current_user.username,
                        email=current_user.email,
                        profile_picture=current_user.profile_picture,
                        post_id=post_id,
                        content=data,
                    )

                    new_comment = models.DBComment(
                        user_id=current_user.id,
                        post_id=post_id,
                        content=data,
                    )

                    db.add(new_comment)
                    await db.commit()
                    await db.refresh(new_comment)
                except Exception as e:
                    print(e)
                    raise HTTPException(status_code=400, detail=str(e))

                try:
                    await manager.broadcast(comment_serializer.json(), post_id, "post")
                except RuntimeError:
                    print("Attempted to send message after WebSocket was closed.")
                except WebSocketDisconnect:
                    print(
                        f"Client #{user_email} disconnected during message broadcast."
                    )
                    break

        except (jwt.ExpiredSignatureError, jwt.exceptions.ExpiredSignatureError):
            # Refresh the token logic
            url = "http://localhost:8000/api/is-authenticated/"
            response = await fetch(url, websocket.cookies)
            set_cookie_header = response.headers.get("Set-Cookie")

            print(set_cookie_header)
            if set_cookie_header:
                match = re.search(r"access_token=([^;]+)", set_cookie_header)
                if match:
                    access_token_value = match.group(1)
                    websocket.cookies["access_token"] = access_token_value
                else:
                    # await websocket.send_text("Failed to refresh access token. Please log in again.")
                    await websocket.close()
                    break
        except (jwt.DecodeError, jwt.InvalidTokenError):
            # await websocket.send_text("Invalid token. Please log in again.")
            await websocket.close()
            break
        except WebSocketDisconnect:
            manager.disconnect(websocket, post_id, "post")
            # print(f"User {user_email} disconnected from post {post_id}.")
            # await manager.broadcast(f"Client #{user_email} left the chat", post_id, "post")
            break
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))


async def get_or_create_conversation(sender_id: int, receiver_id: int, db: AsyncSession):
    query = await db.execute(
        select(models.DBConversation.id)
        .join(models.DBConversationMember, models.DBConversation.id == models.DBConversationMember.conversation_id)
        .where(models.DBConversationMember.user_id.in_([sender_id, receiver_id]))
        .group_by(models.DBConversation.id)
        .having(func.count(models.DBConversationMember.id) == 2)
    )
    conversation_id = query.scalars().first()

    if not conversation_id:
        new_conversation = models.DBConversation(name="New Conversation")
        db.add(new_conversation)
        await db.commit()
        await db.refresh(new_conversation)

        members = [
            models.DBConversationMember(user_id=sender_id, conversation_id=new_conversation.id),
            models.DBConversationMember(user_id=receiver_id, conversation_id=new_conversation.id)
        ]
        db.add_all(members)
        await db.commit()
        await db.refresh(members)
        conversation_id = new_conversation.id
        return conversation_id
    return conversation_id


@app.websocket("/ws/{user_id}/send-message/")
async def websocket_chat(
    websocket: WebSocket,
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    await manager.connect(websocket, user_id, "chat")
    user_email = None
    while True:
        try:
            access_token = websocket.cookies.get("access_token")

            if access_token is None:
                await websocket.close()
                break

            user_data = jwt.decode(
                access_token.encode("utf-8"),
                os.getenv("SECRET_KEY"),
                algorithms=[os.getenv("ALGORITHM")],
            )
            user_email = user_data.get("sub")

            current_user_payload = await db.execute(
                select(models.DBUser).filter(models.DBUser.email == user_email)
            )
            current_user = current_user_payload.scalars().first()

            data = await websocket.receive_json()

            if data:
                try:
                    exists_conversation_id = await get_or_create_conversation(sender_id=current_user.id, receiver_id=user_id, db=db)

                    print(exists_conversation_id)

                    new_message = models.DBMessage(
                        sender_id=current_user.id,
                        receiver_id=user_id,
                        conversation_id=exists_conversation_id,
                        content=data,
                    )
                    db.add(new_message)
                    await db.commit()
                    await db.refresh(new_message)

                    message_serializer = MessageCreate(
                        sender_id=current_user.id,
                        receiver_id=user_id,
                        conversation_id=exists_conversation_id,
                        content=data,
                    )

                except Exception as e:
                    print(e)
                    raise HTTPException(status_code=400, detail=str(e))

                try:

                    await manager.broadcast(message_serializer.json(), user_id, "chat")

                except RuntimeError as e:
                    print(f"Attempted to send message after WebSocket was closed. {e}")
                    await websocket.close()
                    break
                except WebSocketDisconnect:
                    print(
                        f"Client #{user_email} disconnected during message broadcast."
                    )
                    break

        except (jwt.ExpiredSignatureError, jwt.exceptions.ExpiredSignatureError):
            # Refresh the token logic
            url = "http://localhost:8000/api/is-authenticated/"
            response = await fetch(url, websocket.cookies)
            set_cookie_header = response.headers.get("Set-Cookie")

            if set_cookie_header:
                match = re.search(r"access_token=([^;]+)", set_cookie_header)
                if match:
                    access_token_value = match.group(1)
                    websocket.cookies["access_token"] = access_token_value
                else:
                    # await websocket.send_text("Failed to refresh access token. Please log in again.")
                    await websocket.close()
                    break
        except (jwt.DecodeError, jwt.InvalidTokenError):
            # await websocket.send_text("Invalid token. Please log in again.")
            await websocket.close()
            break
        except WebSocketDisconnect:
            manager.disconnect(websocket, user_id, "chat")
            print(f"User {user_email} disconnected from post {user_id}.")
            # await manager.broadcast(f"Client #{user_email} left the chat", chat_id, "chat")
            break
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
