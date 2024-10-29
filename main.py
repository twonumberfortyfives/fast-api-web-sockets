import base64
import os
import re
import uuid

import aiofiles
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

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from chat.serializers import MessageCreate
from db import models
from db.engine import init_db
from dependencies import get_db
from users.routes import router as users_router
from posts.routes import router as posts_router
from chat.routes import router as chat_router
from comments.routes import router as comment_router
from comments.serializers import CommentCreate
from dependencies import encrypt_message

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
                try:
                    await connection.send_text(message)
                except Exception as e:
                    print(f"Error sending message to {connection.client}: {e}")


manager = ConnectionManager()


async def fetch(url, cookies):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, cookies=cookies) as response:
            if response.status == 200:
                return response
            else:
                return {"error": f"Failed to fetch data, status: {response.status}"}


@app.websocket("/ws/posts/{post_id}")
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
            url = "http://localhost:8000/api/is-authenticated/"  # TODO: Change it to new domain before deployment
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


@app.websocket("/ws/chats/{chat_id}")
async def websocket_chat(
        websocket: WebSocket,
        chat_id: int,
        db: AsyncSession = Depends(get_db),
):
    await manager.connect(websocket, chat_id, "chat")
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
            if data.get("content") or data.get("files"):
                try:
                    query_chat_with_current_user = await db.execute(
                        select(models.DBConversation)
                        .outerjoin(
                            models.DBConversationMember,
                            models.DBConversationMember.conversation_id
                            == models.DBConversation.id,
                        )
                        .options(selectinload(models.DBConversation.members))
                        .filter(models.DBConversationMember.user_id == current_user.id)
                        .filter(models.DBConversation.id == chat_id)
                        .distinct()
                    )
                    current_chat = query_chat_with_current_user.scalars().first()

                    query_receiver = await db.execute(
                        select(models.DBConversationMember)
                        .outerjoin(
                            models.DBUser,
                            models.DBConversationMember.user_id == models.DBUser.id,
                        )
                        .options(selectinload(models.DBConversationMember.user))
                        .filter(models.DBConversationMember.conversation_id == chat_id)
                        .filter(models.DBUser.id != current_user.id)
                        .distinct()
                    )
                    receiver = query_receiver.scalars().first()

                    encrypted_data = await encrypt_message(data["content"])
                    encoded_data = base64.b64encode(encrypted_data).decode(
                        "utf-8"
                    )  # change it to string

                    message = models.DBMessage(
                        sender_id=current_user.id,
                        receiver_id=receiver.user.id,
                        conversation_id=current_chat.id,
                        content=encoded_data,
                    )

                    db.add(message)
                    await db.commit()
                    await db.refresh(message)

                    array_with_file_links = []

                    file_data_list = data.get("files", None)
                    if file_data_list:
                        for file_data in file_data_list:
                            file_name = file_data.get('name')
                            binary_data = file_data.get('data')

                            if isinstance(binary_data, list):
                                file_bytes = bytes(binary_data)
                            else:
                                file_bytes = binary_data  # Assuming this is already in bytes

                            print(f"File Name: {file_name}, File Bytes Length: {len(file_bytes)}")

                            file_path = f"uploads/{uuid.uuid4()}_{file_name}"

                            async with aiofiles.open(file_path, "wb") as f:
                                await f.write(file_bytes)

                            new_file = models.DBFileMessage(
                                message_id=message.id,
                                link=f"http://127.0.0.1:8000/{file_path}"  # TODO: change before deploy
                            )
                            db.add(new_file)
                            array_with_file_links.append(new_file)
                            print(f"Successfully wrote file: {file_path}")
                    await db.commit()

                    message_serializer = MessageCreate(
                        sender_id=current_user.id,
                        receiver_id=receiver.user.id,
                        conversation_id=current_chat.id,
                        content=message.content,
                        created_at=message.created_at,
                        files=[file.link for file in array_with_file_links],
                    )

                except Exception as e:
                    print(e)
                    raise HTTPException(status_code=400, detail=str(e))

                try:
                    await manager.broadcast(message_serializer.json(), chat_id, "chat")
                except RuntimeError:
                    print("Attempted to send message after WebSocket was closed.")
                except WebSocketDisconnect:
                    print(
                        f"Client #{user_email} disconnected during message broadcast."
                    )
                    break

        except (jwt.ExpiredSignatureError, jwt.exceptions.ExpiredSignatureError):
            url = "http://localhost:8000/api/is-authenticated/"  # TODO: Change it to new domain before deployment
            response = await fetch(url, websocket.cookies)
            set_cookie_header = response.headers.get("Set-Cookie")

            if set_cookie_header:
                match = re.search(r"access_token=([^;]+)", set_cookie_header)
                if match:
                    access_token_value = match.group(1)
                    websocket.cookies["access_token"] = access_token_value
                else:
                    await websocket.close()
                    break
        except (jwt.DecodeError, jwt.InvalidTokenError):
            await websocket.close()
            break
        except WebSocketDisconnect:
            manager.disconnect(websocket, chat_id, "chat")
            print(f"User {user_email} disconnected from chat {chat_id}.")
            break
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            await websocket.close()
            break
