from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Request

from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from db import models
from dependencies import get_db, get_current_user
from users.routes import router as users_router
from posts.routes import router as posts_router
from chat.routes import router as chat_router
from chat.views import get_or_create_chat


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


@app.get("/")
async def root():
    return {"message": "Hello World"}


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        self.active_connections.pop(user_id, None)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def send_message_to_user(self, user_id: int, message: str):
        connection = self.active_connections.get(user_id)
        if connection:
            await connection.send_text(message)


manager = ConnectionManager()


@app.websocket("/ws/{sender_id}/{receiver_id}")
async def chat(request: Request, websocket: WebSocket, sender_id: int, receiver_id: int, db: AsyncSession = Depends(get_db)):
    try:
        # Authenticate user via token or other method
        user_id = await get_current_user(request=request, db=db)
        if user_id != sender_id:
            # Reject connection if sender ID doesn't match authenticated user
            await websocket.close(code=403)
            return

        # Continue if authentication succeeds
        await manager.connect(websocket, sender_id)
        while True:
            data = await websocket.receive_text()

            chat = await get_or_create_chat(sender_id, receiver_id, db)

            new_message = models.DBMessage(
                chat_id=chat.id,
                sender_id=sender_id,
                content=data,
                created_at=datetime.utcnow()
            )
            db.add(new_message)
            await db.commit()
            await db.refresh(new_message)
            await manager.send_message_to_user(receiver_id, data)

    except WebSocketDisconnect:
        manager.disconnect(sender_id)
