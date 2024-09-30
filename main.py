import os
from datetime import datetime

import jwt
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Request, WebSocketException, Cookie
from fastapi.staticfiles import StaticFiles

from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db import models
from dependencies import get_db, get_current_user
from users.routes import router as users_router
from posts.routes import router as posts_router
from chat.routes import router as chat_router
from chat.views import get_or_create_chat
from users.views import get_user_by_email

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(users_router, prefix="/api", tags=["users"])
app.include_router(posts_router, prefix="/api", tags=["posts"])
app.include_router(chat_router, prefix="/api", tags=["chat"])

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/")
async def root():
    return {"message": "Hello World"}


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket, db: AsyncSession, receiver_id: int):
        access_token = websocket.cookies.get("access_token")
        user_data = jwt.decode(
            access_token,
            os.getenv("SECRET_KEY"),
            algorithms=[os.getenv("ALGORITHM")],
        )
        user_email = user_data.get("sub")
        user_id = (await get_user_by_email(db=db, email=user_email)).id

        db_message = models.DBMessage(
            chat_id=1,
            sender_id=user_id,
            receiver_id=receiver_id,
            content=message,
        )
        db.add(db_message)
        await db.commit()
        await db.refresh(db_message)
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.websocket("/ws/{receiver_id}")
async def websocket_endpoint(websocket: WebSocket, receiver_id: int, db: AsyncSession = Depends(get_db)):
    await manager.connect(websocket)
    access_token = websocket.cookies.get("access_token")
    if not access_token:
        await websocket.close(code=1008)
        return
    if isinstance(access_token, str):
        access_token = access_token.encode('utf-8')

    try:
        user_data = jwt.decode(
            access_token,
            os.getenv("SECRET_KEY"),
            algorithms=[os.getenv("ALGORITHM")],
        )
    except jwt.ExpiredSignatureError:
        await websocket.close(code=1008)
        return
    except jwt.InvalidTokenError:
        await websocket.close(code=1008)
        return

    user_email = user_data["sub"]
    try:
        await manager.send_personal_message(f"Connected as: {user_email}", websocket, db, receiver_id)

        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket, db, receiver_id)
            await manager.broadcast(f"Client #{user_email} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client {user_email} left the chat")
