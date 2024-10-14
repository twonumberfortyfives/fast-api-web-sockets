import json
import os
import re

import aiohttp
import jwt
from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    Request,
)
from fastapi.staticfiles import StaticFiles

from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination, paginate, Page
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db import models
from db.engine import init_db
from dependencies import get_db
from users.routes import router as users_router
from posts.routes import router as posts_router
from chat.routes import router as chat_router
from comments.routes import router as comment_router
from comments.serializers import CommentList
from comments import views

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
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, group_name: int):
        await websocket.accept()
        if group_name not in self.active_connections:
            self.active_connections[group_name] = []
        self.active_connections[group_name].append(websocket)

    def disconnect(self, websocket: WebSocket, group_name: int):
        self.active_connections[group_name].remove(websocket)
        if not self.active_connections[group_name]:
            del self.active_connections[group_name]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, group_name: int):
        if group_name in self.active_connections:
            for connection in self.active_connections[group_name]:
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
async def websocket_endpoint(websocket: WebSocket, post_id: int, db: AsyncSession = Depends(get_db)):
    await manager.connect(websocket, post_id)
    user_email = None
    while True:
        try:
            access_token = websocket.cookies.get("access_token")
            user_data = jwt.decode(
                access_token.encode('utf-8'),
                os.getenv("SECRET_KEY"),
                algorithms=[os.getenv("ALGORITHM")]
            )
            user_email = user_data.get("sub")

            current_user_payload = await db.execute(
                select(models.DBUser)
                .filter(models.DBUser.email == user_email)
            )
            current_user = current_user_payload.scalar()

            data = await websocket.receive_json()

            print(data)

            if data != "":

                try:
                    comment_serializer = CommentList(
                        user_id=current_user.id,
                        username=current_user.username,
                        email=current_user.email,
                        profile_picture=current_user.profile_picture,
                        post_id=post_id,
                        content=data,
                    )

                    new_comment = models.DBComment(
                        user_id=comment_serializer.user_id,
                        post_id=comment_serializer.post_id,
                        content=comment_serializer.content,
                    )

                    db.add(new_comment)
                    await db.commit()
                    await db.refresh(new_comment)
                except Exception as e:
                    raise HTTPException(status_code=400, detail=str(e))

                await manager.broadcast(comment_serializer.json(), post_id)

        except jwt.ExpiredSignatureError:
            url = "http://localhost:8000/api/is-authenticated/"
            response = await fetch(url, websocket.cookies)  # giving the cookies what we have at the moment.
            set_cookie_header = response.headers.get("Set-Cookie")

            match = re.search(r"access_token=([^;]+)", set_cookie_header)
            if match:
                access_token_value = match.group(1)
                websocket.cookies["access_token"] = access_token_value
            else:
                await websocket.send_text("Failed to refresh access token. Please log in again.")
                await websocket.close()
                break
        except WebSocketDisconnect:
            manager.disconnect(websocket, post_id)
            await manager.broadcast(f"Client #{user_email} left the chat", post_id)
            break
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

