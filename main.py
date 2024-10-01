import os

import jwt
from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    Depends,
)
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import HTTPException

from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db import models
from db.engine import init_db
from dependencies import get_db, refresh_token_view
from users.routes import router as users_router
from posts.routes import router as posts_router
from chat.routes import router as chat_router
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


@app.on_event("startup")
async def on_startup():
    await init_db()


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

    async def send_personal_message(
            self, message: str, websocket: WebSocket, db: AsyncSession, receiver_id: int
    ):
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


async def get_current_user_websocket(
    websocket,
    db: AsyncSession = Depends(get_db),
):
    access_token = websocket.cookies.get("access_token")
    refresh_token = websocket.cookies.get("refresh_token")

    if access_token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        user_data = jwt.decode(
            access_token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")]
        )
    except jwt.ExpiredSignatureError:
        print("Token expired, trying to refresh")
        if refresh_token is None:
            raise HTTPException(status_code=401, detail="Refresh token is missing")

        # Call the refresh token view to get new tokens
        new_access_token, new_refresh_token = await refresh_token_view(refresh_token)

        # Send the new tokens back to the client
        await websocket.send_json({
            "type": "token_refresh",
            "access_token": new_access_token,
            "refresh_token": new_refresh_token
        })

        # Decode the new access token
        user_data = jwt.decode(
            new_access_token,
            os.getenv("SECRET_KEY"),
            algorithms=[os.getenv("ALGORITHM")],
        )

    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Could not validate credentials")

    user_email = user_data.get("sub")

    result = await db.execute(
        select(models.DBUser).filter(models.DBUser.email == user_email)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user  # Return the user model


@app.websocket("/send-message/{receiver_id}")
async def websocket_endpoint(
        websocket: WebSocket, receiver_id: int, db: AsyncSession = Depends(get_db)
):
    await manager.connect(websocket)
    try:
        user_id = (await get_current_user_websocket(websocket, db)).id
        if not user_id:
            await websocket.close(code=1008)
            return

        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(data, websocket, db, receiver_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client {user_id} left the chat")
    except Exception as e:
        print(f"Error in WebSocket: {e}")
        await websocket.close(code=1008)
