import jwt
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

import crud
import schemas
from db.engine import SessionLocal

app = FastAPI()


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "Hello World"}


@app.get("/get-users", response_model=list[schemas.User])
def get_users(db: Session = Depends(get_db)):
    return crud.get_all_users(db)


@app.post("/register", response_model=schemas.UserCreate)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_username_validation = crud.get_user_by_username(db, user.username)
    if db_username_validation:
        raise HTTPException(status_code=400, detail="Account with current username already exists!")
    db_email_validation = crud.get_user_by_email(db, user.email)
    if db_email_validation:
        raise HTTPException(status_code=400, detail="Account with current email already exists!")
    return crud.create_user(db=db, user=user)


@app.post("/login", response_model=schemas.UserTokenResponse)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)) -> schemas.UserTokenResponse:
    return crud.login_user(db=db, user=user)


@app.post("/refresh", response_model=schemas.UserTokenResponse)
def refresh_token(user_refresh_token: schemas.RefreshToken):
    try:
        payload = jwt.decode(user_refresh_token.refresh_token, crud.SECRET_KEY, algorithms=[crud.ALGORITHM])
        email = payload.get("sub")

        if not email:
            raise HTTPException(status_code=403, detail="Invalid refresh token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=403, detail="Refresh token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Invalid refresh token")

    new_access_token = crud.create_access_token(data={"sub": email})
    new_refresh_token = crud.create_refresh_token(data={"sub": email})
    return schemas.UserTokenResponse(access_token=new_access_token, refresh_token=new_refresh_token)
