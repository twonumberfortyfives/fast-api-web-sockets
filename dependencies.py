import os
from datetime import datetime, timedelta

import jwt
from fastapi import Depends, Request, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from db.engine import async_session
from sqlalchemy.future import select
from db import models
from db.models import Role

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_TIME = 5
REFRESH_TOKEN_EXPIRE_TIME = 60


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


async def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(seconds=ACCESS_TOKEN_EXPIRE_TIME)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def create_refresh_token(data: dict):
    expire = datetime.utcnow() + timedelta(
        seconds=REFRESH_TOKEN_EXPIRE_TIME
    )  # Very short expiration for debugging
    data.update({"exp": expire})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


async def refresh_token_view(refresh_token: str):
    try:
        payload = jwt.decode(
            refresh_token,
            os.getenv("SECRET_KEY"),
            algorithms=[os.getenv("ALGORITHM")],
        )
        email = payload.get("sub")

        if not email:
            raise HTTPException(status_code=403, detail="Invalid refresh token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=403, detail="Refresh token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Invalid refresh token")
    new_access_token = await create_access_token(data={"sub": email})
    new_refresh_token = await create_refresh_token(data={"sub": email})
    return new_access_token, new_refresh_token


async def get_current_user(
    request: Request, response: Response, db: AsyncSession = Depends(get_db)
):
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    if access_token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        user_data = jwt.decode(
            access_token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")]
        )
    except jwt.ExpiredSignatureError:
        print("TRYING TO MAKE NEW REFRESH")
        if refresh_token is None:
            raise HTTPException(status_code=401, detail="Refresh token is missing")

        # Call the refresh token view to get new tokens
        new_access_token, new_refresh_token = await refresh_token_view(refresh_token)

        response.set_cookie(key="access_token", value=new_access_token, httponly=True)
        response.set_cookie(key="refresh_token", value=new_refresh_token, httponly=True)

        # Changing the variable from try block. Putting there new refreshed access token!
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


def require_role(required_role: Role):
    async def role_checker(current_user: models.DBUser = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=403,
                detail="You are not allowed to perform this action",
            )
        return current_user

    return role_checker
