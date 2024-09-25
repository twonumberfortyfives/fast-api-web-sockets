from datetime import timedelta, datetime

import jwt
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import Response, Request
from dotenv import load_dotenv
from sqlalchemy.orm import selectinload
import os

from db import models
from dependencies import get_current_user
from users import serializers

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 30


async def get_users_view(db: AsyncSession):
    result = await db.execute(
        select(models.DBUser)
        .outerjoin(models.DBPost)
        .options(selectinload(models.DBUser.posts))
    )
    return result


async def retrieve_user_view(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(models.DBUser)
        .outerjoin(models.DBPost)
        .options(selectinload(models.DBUser.posts))
        .filter(models.DBUser.id == user_id)
    )
    user = result.scalar()
    return user


async def get_user_by_username(db: AsyncSession, username: str):
    result = await db.execute(
        select(models.DBUser).filter(models.DBUser.username == username)
    )
    user = result.scalar_one_or_none()
    return user


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(
        select(models.DBUser).filter(models.DBUser.email == email)
    )
    user = result.scalar_one_or_none()
    return user


async def get_user_model(access_token: str, db: AsyncSession):
    if not access_token:
        raise HTTPException(status_code=403, detail="Not Authorized")
    payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
    user_email = payload.get("sub")
    result = await db.execute(
        select(models.DBUser).filter(models.DBUser.email == user_email)
    )
    user_model = result.scalar_one_or_none()
    return user_model


async def hash_password(password: str):
    return pwd_context.hash(password)


async def verify_password(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)


async def register_view(db: AsyncSession, user: serializers.UserCreate):
    hashed_password = await hash_password(user.password)
    db_user = models.DBUser(
        email=user.email,
        username=user.username,
        password=hashed_password,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def create_refresh_token(data: dict):
    expire = datetime.now() + timedelta(days=30)
    data.update({"exp": expire})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


async def login_view(
    db: AsyncSession, user: serializers.UserLogin
) -> serializers.UserTokenResponse:
    found_user = await get_user_by_email(email=user.email, db=db)
    verified_password = await verify_password(user.password, found_user.password)
    if not verified_password:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    refresh_token = await create_refresh_token(data={"sub": user.email})

    return serializers.UserTokenResponse(
        access_token=access_token, refresh_token=refresh_token
    )


async def my_profile_view(request: Request, db: AsyncSession):
    user_id = (await get_current_user(request=request, db=db)).id
    user = await retrieve_user_view(db=db, user_id=user_id)
    return user


async def my_profile_edit_view(
    request: Request, user: serializers.UserEdit, db: AsyncSession
):
    found_user = await get_current_user(request=request, db=db)
    found_user.username = user.username
    found_user.email = user.email

    await db.commit()
    await db.refresh(found_user)

    return found_user


async def change_password_view(
    request: Request, password: serializers.UserPasswordEdit, db: AsyncSession
):
    user = await get_current_user(request=request, db=db)
    if await verify_password(password.old_password, user.password) and user:
        new_hashed_password = await hash_password(password.new_password)
        user.password = new_hashed_password
        await db.commit()
        await db.refresh(user)
        return True
    return False


async def is_authenticated_view(request: Request, db: AsyncSession):
    user = await get_current_user(db=db, request=request)
    if user:
        return True
    else:
        return False


async def logout_view(response: Response, request: Request):
    try:
        access_token = request.cookies.get("access_token")
        refresh_token = request.cookies.get("refresh_token")

        if not access_token and not refresh_token:
            raise HTTPException(status_code=400, detail="You are not authorized")
        response.delete_cookie(key="access_token")
        response.delete_cookie(key="refresh_token")
        return {"message": "Logout successful"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


async def delete_my_account_view(request: Request, response: Response, db: AsyncSession):
    user = await get_current_user(request=request, db=db)
    await db.delete(user)
    await db.commit()
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return True


async def refresh_token_view(user_refresh_token: serializers.RefreshToken):
    try:
        payload = jwt.decode(
            user_refresh_token.refresh_token,
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
    response = JSONResponse(status_code=200, content={"message": "Token updated."})
    response.set_cookie(
        key="access_token", value=new_access_token, httponly=True, samesite="strict"
    )
    response.set_cookie(
        key="refresh_token", value=new_refresh_token, httponly=True, samesite="strict"
    )
    return response
