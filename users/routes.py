from fastapi import APIRouter, Request, Depends, Response, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi_limiter.depends import RateLimiter
from fastapi_pagination import Page, paginate

from sqlalchemy.ext.asyncio import AsyncSession

from db import models
from dependencies import get_db, require_role
from users import views, serializers
from posts.serializers import PostList


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


@router.get(
    "/users",
    # dependencies=[Depends(RateLimiter(times=120, seconds=60))],
)
async def get_users(db: AsyncSession = Depends(get_db)) -> Page[serializers.UserList]:
    return paginate(await views.get_users_view(db=db))


@router.get(
    "/users/{user}",
    # dependencies=[Depends(RateLimiter(times=120, seconds=60))],
)
async def retrieve_user(
    user, db: AsyncSession = Depends(get_db)
) -> Page[serializers.UserList]:
    return paginate(await views.retrieve_user_view(db=db, user=user))


@router.get(
    "/users/{user_id}/posts",
    # dependencies=[Depends(RateLimiter(times=120, seconds=60))],
)
async def retrieve_users_posts(
    user_id: int,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> Page[PostList]:
    return paginate(
        await views.retrieve_users_posts_view(
            user_id=user_id, request=request, response=response, db=db
        )
    )


@router.get(
    "/my-profile",
    response_model=serializers.UserMyProfile,
    # dependencies=[Depends(RateLimiter(times=120, seconds=60))],
)
async def my_profile(
    request: Request, response: Response, db: AsyncSession = Depends(get_db)
):
    return await views.my_profile_view(request=request, response=response, db=db)


@router.patch(
    "/my-profile",
    response_model=serializers.UserList,
    # dependencies=[Depends(RateLimiter(times=120, seconds=60))],
)
async def my_profile_edit(
    request: Request,
    response: Response,
    email: str = None,
    username: str = None,
    bio: str = None,
    profile_picture: UploadFile | str = File(None),
    db: AsyncSession = Depends(get_db),
):
    return await views.my_profile_edit_view(
        request=request,
        response=response,
        username=username,
        email=email,
        bio=bio,
        profile_picture=profile_picture,
        db=db,
    )


@router.patch(
    "/my-profile/change-password",
    # dependencies=[Depends(RateLimiter(times=120, seconds=60))],
)
async def change_password(
    request: Request,
    response: Response,
    password: serializers.UserPasswordEdit,
    db: AsyncSession = Depends(get_db),
):
    return await views.change_password_view(
        request=request, response=response, password=password, db=db
    )


@router.post(
    "/register",
    # dependencies=[Depends(RateLimiter(times=120, seconds=60))],
)
async def register(user: serializers.UserCreate, db: AsyncSession = Depends(get_db)):
    user = await views.register_view(db=db, user=user)
    return JSONResponse({"message": f"{user.username} has been registered."})


@router.post(
    "/login",
    # dependencies=[Depends(RateLimiter(times=120, seconds=60))],
)
async def login(user: serializers.UserLogin, db: AsyncSession = Depends(get_db)):
    user_tokens = await views.login_view(db=db, user=user)

    response = JSONResponse(content={"message": "Login successful."}, status_code=200)
    response.set_cookie(
        key="access_token",
        value=user_tokens.access_token,
        httponly=True,
        samesite="none",
        secure=False,
    )
    response.set_cookie(
        key="refresh_token",
        value=user_tokens.refresh_token,
        httponly=True,
        samesite="none",
        secure=False,
    )

    return response


@router.post(
    "/logout",
    # dependencies=[Depends(RateLimiter(times=120, seconds=60))],
)
async def logout(response: Response, request: Request):
    return await views.logout_view(response, request)


@router.delete(
    "/my-profile",
    # dependencies=[Depends(RateLimiter(times=120, seconds=60))],
)
async def delete_my_account(
    request: Request,
    response: Response,
    password_confirm: serializers.UserDeleteAccountPasswordConfirm,
    db: AsyncSession = Depends(get_db),
):
    result = await views.delete_my_account_view(
        request=request, response=response, password_confirm=password_confirm, db=db
    )
    if result:
        return {"message": "Your account has been deleted."}
