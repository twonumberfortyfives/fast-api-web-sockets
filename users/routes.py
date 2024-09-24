import jwt
from fastapi import APIRouter, Request, Depends, HTTPException, Response
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession

from db import models
from dependencies import get_db, require_role
from users import views, serializers

router = APIRouter()


@router.get("/is-authenticated")
async def is_authenticated(request: Request, db: AsyncSession = Depends(get_db)):
    access_token = request.cookies.get("access_token")
    is_user = await views.is_authenticated(access_token=access_token, db=db)
    if access_token and is_user:
        return JSONResponse(status_code=200, content={"is_authenticated": True})
    else:
        raise HTTPException(status_code=401, detail="Not authenticated")


@router.get("/admin-only")
async def get_admin_end_point(
    current_user: models.DBUser = Depends(require_role(models.Role.admin)),
):
    return {"message": "Welcome admin!"}


@router.get("/get-users", response_model=list[serializers.UserList])
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await views.get_all_users(db=db)
    users = result.scalars().all()
    return users


@router.get("/get-users/{user_id}", response_model=serializers.UserList)
async def retrieve_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await views.retrieve_user(db=db, user_id=user_id)
    if user:
        return user
    raise HTTPException(status_code=404, detail="User not found")


@router.put("/my-profile", response_model=serializers.UserEdit)
async def my_profile(
    request: Request, user: serializers.UserEdit, db: AsyncSession = Depends(get_db)
):
    access_token = request.cookies.get("access_token")
    user = await views.my_profile(access_token=access_token, user=user, db=db)
    return user


@router.patch("/my-profile/change-password")
async def change_password(
    request: Request,
    password: serializers.UserPasswordEdit,
    db: AsyncSession = Depends(get_db),
):
    access_token = request.cookies.get("access_token")
    result = await views.change_password(
        access_token=access_token, password=password, db=db
    )
    if result:
        return {"message": "Password changed successfully"}
    raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/register")
async def register(user: serializers.UserCreate, db: AsyncSession = Depends(get_db)):
    db_username_validation = await views.get_user_by_username(
        db=db, username=user.username
    )
    if db_username_validation:
        raise HTTPException(
            status_code=400, detail="Account with current username already exists!"
        )
    db_email_validation = await views.get_user_by_email(db=db, email=user.email)
    if db_email_validation:
        raise HTTPException(
            status_code=400, detail="Account with current email already exists!"
        )
    user = await views.create_user(db=db, user=user)
    response = JSONResponse({"message": f"{user.username} has been registered."})
    return response


@router.post("/login")
async def login(user: serializers.UserLogin, db: AsyncSession = Depends(get_db)):
    user_tokens = await views.login_user(db=db, user=user)

    response = JSONResponse(content={"message": "Login successful."}, status_code=200)
    response.set_cookie(
        key="access_token",
        value=user_tokens.access_token,
        httponly=True,
        samesite="strict",
    )
    response.set_cookie(
        key="refresh_token",
        value=user_tokens.refresh_token,
        httponly=True,
        samesite="strict",
    )

    return response


@router.post("/logout")
async def logout(response: Response, request: Request):
    return await views.logout(response, request)


@router.post("/refresh")
async def refresh_token(user_refresh_token: serializers.RefreshToken):
    try:
        payload = jwt.decode(
            user_refresh_token.refresh_token,
            views.SECRET_KEY,
            algorithms=[views.ALGORITHM],
        )
        email = payload.get("sub")

        if not email:
            raise HTTPException(status_code=403, detail="Invalid refresh token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=403, detail="Refresh token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Invalid refresh token")

    new_access_token = await views.create_access_token(data={"sub": email})
    new_refresh_token = await views.create_refresh_token(data={"sub": email})
    response = JSONResponse(status_code=200, content={"message": "Token updated."})
    response.set_cookie(
        key="access_token", value=new_access_token, httponly=True, samesite="strict"
    )
    response.set_cookie(
        key="refresh_token", value=new_refresh_token, httponly=True, samesite="strict"
    )
    return response
