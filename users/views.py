import json
import os
import uuid

import aioredis
from fastapi import HTTPException, UploadFile
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import Response, Request
from dotenv import load_dotenv
from sqlalchemy.orm import selectinload

from db import models
from dependencies import (
    get_current_user,
    create_access_token,
    create_refresh_token,
    ACCESS_TOKEN_EXPIRE_TIME_MINUTES,
)
from users import serializers

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def get_users_from_db(db: AsyncSession):
    result = await db.execute(select(models.DBUser))
    users = result.scalars().all()
    return users


async def get_users_view(db: AsyncSession):
    users = await get_users_from_db(db)

    if users:

        return users
    raise HTTPException(status_code=404, detail="Users not found")


async def retrieve_user_view(db: AsyncSession, user):
    if user.isdigit():
        user = int(user)
        result = await db.execute(
            select(models.DBUser).filter(models.DBUser.id == user)
        )
        user = result.scalar()
    if isinstance(user, str):
        result = await db.execute(
            select(models.DBUser).filter(models.DBUser.username.ilike(f"%{user}%"))
        )
        user = result.scalars().all()
    if user:
        return user
    raise HTTPException(status_code=404, detail="User not found")


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


async def hash_password(password: str):
    return pwd_context.hash(password)


async def verify_password(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)


async def register_view(db: AsyncSession, user: serializers.UserCreate):
    db_username_validation = await get_user_by_username(db=db, username=user.username)
    if db_username_validation:
        raise HTTPException(
            status_code=400, detail="Account with current username already exists!"
        )
    db_email_validation = await get_user_by_email(db=db, email=user.email)
    if db_email_validation:
        raise HTTPException(
            status_code=400, detail="Account with current email already exists!"
        )

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


async def login_view(
    db: AsyncSession, user: serializers.UserLogin
) -> serializers.UserTokenResponse:
    found_user = await get_user_by_email(email=user.email, db=db)
    if found_user:
        verified_password = await verify_password(user.password, found_user.password)
        if not verified_password:
            raise HTTPException(status_code=400, detail="Incorrect email or password")

        access_token_expires = ACCESS_TOKEN_EXPIRE_TIME_MINUTES
        access_token = await create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        refresh_token = await create_refresh_token(data={"sub": user.email})

        return serializers.UserTokenResponse(
            access_token=access_token, refresh_token=refresh_token
        )
    raise HTTPException(status_code=404, detail="User not found")


async def my_profile_view(request: Request, response: Response, db: AsyncSession):
    # redis_client = await aioredis.from_url("redis://localhost:6379/0")
    return await get_current_user(request=request, response=response, db=db)


async def retrieve_users_posts_view(user_id: int, db: AsyncSession):
    result = await db.execute(
        select(models.DBPost)
        .outerjoin(models.DBUser)
        .options(selectinload(models.DBPost.user))
        .outerjoin(models.DBPostLike)
        .options(selectinload(models.DBPost.likes))
        .outerjoin(models.DBComment, models.DBComment.post_id == models.DBPost.id)
        .options(selectinload(models.DBPost.comments))
        .filter(models.DBPost.user_id == user_id)
        .distinct()
        .order_by(models.DBPost.id.desc())  # Sort by ID in descending order
    )
    users_posts = result.scalars().all()
    return users_posts


async def my_profile_edit_view(
    request: Request,
    response: Response,
    username: str,
    email: str,
    bio: str,
    db: AsyncSession,
    profile_picture: UploadFile = None,
):
    found_user = await get_current_user(request=request, response=response, db=db)

    # Validate and update username
    if username is not None:
        if not username.strip():
            raise HTTPException(
                status_code=400,
                detail="Username cannot be empty or contain only spaces.",
            )
        found_user.username = username

    # Validate and update email
    if email is not None:
        if not email.strip():
            raise HTTPException(
                status_code=400, detail="Email cannot be empty or contain only spaces."
            )
        if "@" not in email:
            raise HTTPException(status_code=400, detail="Invalid email format.")
        found_user.email = email

    # Validate and update bio
    if bio is not None:
        if len(bio) > 500:
            raise HTTPException(
                status_code=400, detail="Bio cannot exceed 500 characters."
            )
        found_user.bio = bio
    if bio is None:
        found_user.bio = bio

    # Handle profile picture upload
    if profile_picture:
        if profile_picture.content_type not in ["image/png", "image/jpeg"]:
            raise HTTPException(status_code=400, detail="Picture type not supported")

        os.makedirs("uploads", exist_ok=True)

        # Save the profile picture
        image_path = (
            f"uploads/{found_user.id}_{uuid.uuid4()}_{profile_picture.filename}"
        )

        with open(image_path, "wb") as f:
            f.write(await profile_picture.read())

        if (
            found_user.profile_picture
            and found_user.profile_picture
            != "http://127.0.0.1:8000/uploads/default.jpg"
        ):
            old_image_path = found_user.profile_picture.split("/")[
                -1
            ]  # Get the filename from the URL
            old_image_full_path = os.path.join(
                "uploads", old_image_path
            )  # Construct the full path
            if os.path.exists(old_image_full_path):
                os.remove(old_image_full_path)

        # Store the URL for accessing the image
        found_user.profile_picture = f"http://127.0.0.1:8000/{image_path}"

    # Commit changes to the database
    try:
        await db.commit()
        await db.refresh(found_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    return found_user


async def change_password_view(
    request: Request,
    response: Response,
    password: serializers.UserPasswordEdit,
    db: AsyncSession,
):
    user = await get_current_user(request=request, response=response, db=db)
    if await verify_password(password.old_password, user.password) and user:
        new_hashed_password = await hash_password(password.new_password)
        user.password = new_hashed_password
        await db.commit()
        await db.refresh(user)
        result = True
    else:
        result = False

    if result:
        return {"message": "Password changed successfully"}
    raise HTTPException(status_code=401, detail="Invalid credentials")


async def is_authenticated_view(request: Request, response: Response, db: AsyncSession):
    user = await get_current_user(db=db, request=request, response=response)
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


async def delete_my_account_view(
    request: Request,
    response: Response,
    password_confirm: serializers.UserDeleteAccountPasswordConfirm,
    db: AsyncSession
):
    user = await get_current_user(request=request, response=response, db=db)

    if await verify_password(password_confirm.password, user.password):
        await db.delete(user)
        await db.commit()
        response.delete_cookie(key="access_token")
        response.delete_cookie(key="refresh_token")
        return True
    else:
        raise HTTPException(status_code=400, detail="Invalid credentials")
