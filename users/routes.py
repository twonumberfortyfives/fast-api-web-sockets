import hashlib
import json

from fastapi import APIRouter, Request, Depends, Response, UploadFile, File
from fastapi.responses import JSONResponse, Response as FastAPIResponse
from fastapi.exceptions import HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from db import models
from dependencies import get_db, require_role
from posts.views import serialize
from users import views, serializers
from users.serializers import UserEdit

router = APIRouter()


@router.get("/is-authenticated")
async def is_authenticated(
    request: Request, response: Response, db: AsyncSession = Depends(get_db)
):
    return await views.is_authenticated_view(request=request, response=response, db=db)


@router.get("/admin-only")
async def get_admin_end_point(
    current_user: models.DBUser = Depends(require_role(models.Role.admin)),
):
    return {"message": "Welcome admin!"}


@router.get("/users", response_model=list[serializers.UserList])
async def get_users(db: AsyncSession = Depends(get_db)):
    return await views.get_users_view(db=db)


@router.get(
    "/users/{user}", response_model=serializers.UserList | list[serializers.UserList]
)
async def retrieve_user(user, db: AsyncSession = Depends(get_db)):
    return await views.retrieve_user_view(db=db, user=user)


@router.get(
    "/users/{user_id}/posts/",
    response_model=list[serializers.UserPosts]
)
async def retrieve_users_posts(user_id: int, response: Response, page: int = None, page_size: int = None, db: AsyncSession = Depends(get_db)):
    if page and page_size:
        all_users_posts = await views.get_all_users_posts_in_total(db=db, user_id=user_id)
        response.headers["X-all-posts-count"] = f"{len(all_users_posts)}"
        return await views.retrieve_users_posts_view(user_id=user_id, page=page, page_size=page_size, db=db)
    return await views.retrieve_users_posts_view(user_id=user_id, page=page, page_size=page_size, db=db)


@router.get("/my-profile", response_model=serializers.UserMyProfile)
async def my_profile(
    request: Request, response: Response, db: AsyncSession = Depends(get_db)
):
    return await views.my_profile_view(request=request, response=response, db=db)


@router.patch("/my-profile", response_model=serializers.UserList)
async def my_profile_edit(
    request: Request,
    response: Response,
    email: str = None,
    username: str = None,
    bio: str = None,
    profile_picture: UploadFile | str = File(None),
    db: AsyncSession = Depends(get_db),
):
    updated_user = await views.my_profile_edit_view(
        request=request,
        response=response,
        username=username,
        email=email,
        bio=bio,
        profile_picture=profile_picture,
        db=db,
    )
    return updated_user


@router.patch("/my-profile/change-password")
async def change_password(
    request: Request,
    response: Response,
    password: serializers.UserPasswordEdit,
    db: AsyncSession = Depends(get_db),
):
    result = await views.change_password_view(
        request=request, response=response, password=password, db=db
    )
    return result


@router.post("/register")
async def register(user: serializers.UserCreate, db: AsyncSession = Depends(get_db)):
    user = await views.register_view(db=db, user=user)
    response = JSONResponse({"message": f"{user.username} has been registered."})
    return response


@router.post("/login")
async def login(user: serializers.UserLogin, db: AsyncSession = Depends(get_db)):
    user_tokens = await views.login_view(db=db, user=user)

    response = JSONResponse(content={"message": "Login successful."}, status_code=200)
    response.set_cookie(
        key="access_token",
        value=user_tokens.access_token,
        httponly=True,
        samesite=None,
        # secure=True set this param in production (HTTPS requests)
    )
    response.set_cookie(
        key="refresh_token",
        value=user_tokens.refresh_token,
        httponly=True,
        samesite=None,
        # secure=True set this param in production (HTTPS requests)
    )

    return response


@router.post("/logout")
async def logout(response: Response, request: Request):
    return await views.logout_view(response, request)


@router.delete("/my-profile")
async def delete_my_account(
    request: Request, response: Response, db: AsyncSession = Depends(get_db)
):
    result = await views.delete_my_account_view(
        request=request, response=response, db=db
    )
    if result:
        return {"message": "Your account has been deleted."}
