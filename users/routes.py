import jwt
from fastapi import APIRouter, Request, Depends, HTTPException, Response
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession

from db import models
from dependencies import get_db, require_role
from users import views, serializers
from users.views import refresh_token_view

router = APIRouter()


@router.get("/is-authenticated")
async def is_authenticated(request: Request, db: AsyncSession = Depends(get_db)):
    is_user = await views.is_authenticated_view(request=request, db=db)
    return is_user


@router.get("/admin-only")
async def get_admin_end_point(
    current_user: models.DBUser = Depends(require_role(models.Role.admin)),
):
    return {"message": "Welcome admin!"}


@router.get("/get-users", response_model=list[serializers.UserList])
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await views.get_users_view(db=db)
    users = result.scalars().all()
    return users


@router.get("/get-users/{user_id}", response_model=serializers.UserList)
async def retrieve_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await views.retrieve_user_view(db=db, user_id=user_id)
    if user:
        return user
    raise HTTPException(status_code=404, detail="User not found")


@router.get("/my-profile", response_model=serializers.UserList)
async def my_profile(request: Request, db: AsyncSession = Depends(get_db)):
    user = await views.my_profile_view(request=request, db=db)
    return user


@router.put("/my-profile/edit", response_model=serializers.UserEdit)
async def my_profile_edit(
    request: Request, user: serializers.UserEdit, db: AsyncSession = Depends(get_db)
):
    user = await views.my_profile_edit_view(request=request, user=user, db=db)
    return user


@router.patch("/my-profile/change-password")
async def change_password(
    request: Request,
    password: serializers.UserPasswordEdit,
    db: AsyncSession = Depends(get_db),
):
    result = await views.change_password_view(request=request, password=password, db=db)
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
    user = await views.register_view(db=db, user=user)
    response = JSONResponse({"message": f"{user.username} has been registered."})
    return response


@router.post("/login")
async def login(
    request: Request, user: serializers.UserLogin, db: AsyncSession = Depends(get_db)
):
    user_tokens = await views.login_view(db=db, user=user, request=request)

    response = JSONResponse(content={"message": "Login successful."}, status_code=200)
    response.set_cookie(
        key="access_token",
        value=user_tokens.access_token,
        httponly=True,
        samesite="strict",
        # secure=True set this param in production (HTTPS requests)
    )
    response.set_cookie(
        key="refresh_token",
        value=user_tokens.refresh_token,
        httponly=True,
        samesite="strict",
        # secure=True set this param in production (HTTPS requests)
    )

    return response


@router.post("/logout")
async def logout(response: Response, request: Request):
    return await views.logout_view(response, request)


@router.post("/refresh")
async def refresh_token(user_refresh_token: serializers.RefreshToken):
    return await refresh_token_view(user_refresh_token)


@router.delete("/delete-my-account")
async def delete_my_account(request: Request, db: AsyncSession = Depends(get_db)):
    result = await views.delete_my_account_view(request=request, db=db)
    if result:
        return {"message": "Your account has been deleted."}
