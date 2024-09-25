from datetime import timedelta, datetime

import jwt
from fastapi import HTTPException
from jose import JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import Response, Request
from dotenv import load_dotenv
from sqlalchemy.orm import selectinload
import os

from db import models
from users import serializers

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


async def get_all_users(db: AsyncSession):
    result = await db.execute(
        select(models.DBUser)
        .outerjoin(models.DBPost)
        .options(selectinload(models.DBUser.posts))
    )
    return result


async def retrieve_user(db: AsyncSession, user_id: int):
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


async def create_user(db: AsyncSession, user: serializers.UserCreate):
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


async def login_user(
    db: AsyncSession, user: serializers.UserLogin
) -> serializers.UserTokenResponse:
    result = await db.execute(
        select(models.DBUser).filter(models.DBUser.email == user.email)
    )
    found_user = result.scalar_one_or_none()
    if not found_user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

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


async def my_profile(access_token: str, db: AsyncSession):
    user_id = (await get_user_model(access_token=access_token, db=db)).id
    user = await retrieve_user(db=db, user_id=user_id)
    return user


async def my_profile_edit(access_token: str, user: serializers.UserEdit, db: AsyncSession):
    try:
        if not access_token:
            raise HTTPException(status_code=403, detail="Not authorized")
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")

        result = await db.execute(
            select(models.DBUser).filter(models.DBUser.email == user_email)
        )

        found_user = result.scalar_one_or_none()

        if found_user is None:
            raise HTTPException(status_code=404, detail="User not found")

        found_user.username = user.username
        found_user.email = user.email

        await db.commit()
        await db.refresh(found_user)

        return found_user

    except JWTError:
        raise HTTPException(status_code=403, detail="Could not validate credentials")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def change_password(
    access_token, password: serializers.UserPasswordEdit, db: AsyncSession
):
    user = await get_user_model(access_token=access_token, db=db)
    if await verify_password(password.old_password, user.password) and user:
        new_hashed_password = await hash_password(password.new_password)
        user.password = new_hashed_password
        await db.commit()
        await db.refresh(user)
        return True
    return False


async def is_authenticated(access_token: str, db: AsyncSession):
    if not access_token:
        return False

    try:
        user_data = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = user_data.get("sub")

        if not user_email:
            return False

        result = await db.execute(
            select(models.DBUser).filter(models.DBUser.email == user_email)
        )
        user = result.scalar()

        return user is not None

    except jwt.ExpiredSignatureError:
        return False
    except jwt.PyJWTError:
        return False


async def logout(response: Response, request: Request):
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


async def delete_my_account(access_token: str, db: AsyncSession):
    user = await get_user_model(access_token=access_token, db=db)
    if not user:
        raise HTTPException(status_code=403, detail="Not authorized")
    await db.delete(user)
    await db.commit()
    return True
