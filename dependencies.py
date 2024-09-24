import jwt
from fastapi import Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.engine import async_session
from sqlalchemy.future import select
from users.views import SECRET_KEY, ALGORITHM
from db import models
from db.models import Role


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    access_token = request.cookies.get("access_token")
    if access_token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        user_data = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Could not validate credentials")

    user_email = user_data.get("sub")
    result = await db.execute(
        select(models.DBUser).filter(models.DBUser.email == user_email)
    )
    user = result.scalar_one_or_none()  # Returns one row or None
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user


def require_role(required_role: Role):
    async def role_checker(current_user: models.DBUser = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=403,
                detail="You are not allowed to perform this action",
            )
        return current_user

    return role_checker
