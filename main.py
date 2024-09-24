import jwt
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

import crud
import schemas
from dependencies import get_db, require_role
from db import models

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/is-authenticated")
async def is_authenticated(request: Request, db: AsyncSession = Depends(get_db)):
    access_token = request.cookies.get("access_token")
    is_user = await crud.is_authenticated(access_token=access_token, db=db)
    if access_token and is_user:
        return JSONResponse(status_code=200, content={"is_authenticated": True})
    else:
        raise HTTPException(status_code=401, detail="Not authenticated")


@app.get("/admin-only")
async def get_admin_end_point(
    current_user: models.DBUser = Depends(require_role(models.Role.admin)),
):
    return {"message": "Welcome admin!"}


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/get-users", response_model=list[schemas.UserList])
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await crud.get_all_users(db=db)
    users = result.scalars().all()
    return users


@app.get("/get-users/{user_id}", response_model=schemas.UserList)
async def retrieve_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await crud.retrieve_user(db=db, user_id=user_id)
    if user:
        return user
    raise HTTPException(status_code=404, detail="User not found")


@app.put("/my-profile", response_model=schemas.UserEdit)
async def my_profile(
    request: Request, user: schemas.UserEdit, db: AsyncSession = Depends(get_db)
):
    access_token = request.cookies.get("access_token")
    user = await crud.my_profile(access_token=access_token, user=user, db=db)
    return user


@app.patch("/my-profile/change-password")
async def change_password(
    request: Request,
    password: schemas.UserPasswordEdit,
    db: AsyncSession = Depends(get_db),
):
    access_token = request.cookies.get("access_token")
    result = await crud.change_password(
        access_token=access_token, password=password, db=db
    )
    if result:
        return {"message": "Password changed successfully"}
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/register")
async def register(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    db_username_validation = await crud.get_user_by_username(
        db=db, username=user.username
    )
    if db_username_validation:
        raise HTTPException(
            status_code=400, detail="Account with current username already exists!"
        )
    db_email_validation = await crud.get_user_by_email(db=db, email=user.email)
    if db_email_validation:
        raise HTTPException(
            status_code=400, detail="Account with current email already exists!"
        )
    user = await crud.create_user(db=db, user=user)
    response = JSONResponse({"message": f"{user.username} has been registered."})
    return response


@app.post("/login")
async def login(user: schemas.UserLogin, db: AsyncSession = Depends(get_db)):
    user_tokens = await crud.login_user(db=db, user=user)

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


@app.post("/refresh")
async def refresh_token(user_refresh_token: schemas.RefreshToken):
    try:
        payload = jwt.decode(
            user_refresh_token.refresh_token,
            crud.SECRET_KEY,
            algorithms=[crud.ALGORITHM],
        )
        email = payload.get("sub")

        if not email:
            raise HTTPException(status_code=403, detail="Invalid refresh token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=403, detail="Refresh token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Invalid refresh token")

    new_access_token = await crud.create_access_token(data={"sub": email})
    new_refresh_token = await crud.create_refresh_token(data={"sub": email})
    response = JSONResponse(status_code=200, content={"message": "Token updated."})
    response.set_cookie(
        key="access_token", value=new_access_token, httponly=True, samesite="strict"
    )
    response.set_cookie(
        key="refresh_token", value=new_refresh_token, httponly=True, samesite="strict"
    )
    return response


@app.get("/get-posts", response_model=list[schemas.Post])
async def get_all_posts(db: AsyncSession = Depends(get_db)):
    return await crud.get_all_posts(db)


@app.post("/create-post", response_model=schemas.Post)
async def create_post(
    request: Request, post: schemas.PostCreate, db: AsyncSession = Depends(get_db)
):
    access_token = request.cookies.get("access_token")
    response = await crud.create_post(db=db, access_token=access_token, post=post)
    return response
