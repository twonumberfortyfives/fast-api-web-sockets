import jwt
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
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


@app.get("/admin-only", dependencies=[Depends(require_role(models.Role.admin))])
def get_admin_end_point():
    return {"message": "Welcome admin!"}


@app.get("/")
def root():
    return {"message": "Hello World"}


@app.get("/get-users", response_model=list[schemas.UserList])
def get_users(db: Session = Depends(get_db)):
    return crud.get_all_users(db)


@app.get("/get-users/{user_id}", response_model=schemas.UserList)
def retrieve_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.retrieve_user(db=db, user_id=user_id)
    if user:
        return user
    raise HTTPException(status_code=404, detail="User not found")


@app.put("/my-profile", response_model=schemas.UserEdit)
def my_profile(request: Request, user: schemas.UserEdit, db: Session = Depends(get_db)):
    access_token = request.cookies.get("access_token")
    user = crud.my_profile(access_token=access_token, user=user, db=db)
    return user


@app.patch("/my-profile/change-password")
def change_password(request: Request, password: schemas.UserPasswordEdit, db: Session = Depends(get_db)):
    access_token = request.cookies.get("access_token")
    if crud.change_password(access_token=access_token, password=password, db=db):
        return {"message": "Password changed successfully"}
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_username_validation = crud.get_user_by_username(db, user.username)
    if db_username_validation:
        raise HTTPException(
            status_code=400, detail="Account with current username already exists!"
        )
    db_email_validation = crud.get_user_by_email(db, user.email)
    if db_email_validation:
        raise HTTPException(
            status_code=400, detail="Account with current email already exists!"
        )
    user = crud.create_user(db=db, user=user)
    response = JSONResponse({"message": f"{user.username} has been registered."})
    return response


@app.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    user_tokens = crud.login_user(db=db, user=user)

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
def refresh_token(user_refresh_token: schemas.RefreshToken):
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

    new_access_token = crud.create_access_token(data={"sub": email})
    new_refresh_token = crud.create_refresh_token(data={"sub": email})
    response = JSONResponse(status_code=200, content={"message": "Token updated."})
    response.set_cookie(
        key="access_token", value=new_access_token, httponly=True, samesite="strict"
    )
    response.set_cookie(
        key="refresh_token", value=new_refresh_token, httponly=True, samesite="strict"
    )
    return response


@app.get("/get-posts", response_model=list[schemas.Post])
def get_all_posts(db: Session = Depends(get_db)):
    return crud.get_all_posts(db)


@app.post("/create-post", response_model=schemas.Post)
def create_post(
    request: Request, post: schemas.PostCreate, db: Session = Depends(get_db)
):
    access_token = request.cookies.get("access_token")
    response = crud.create_post(db=db, access_token=access_token, post=post)
    return response
