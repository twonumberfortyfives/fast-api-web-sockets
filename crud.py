from datetime import timedelta, datetime

import jwt
from fastapi import HTTPException
from jose import JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

from db import models
import schemas

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def get_all_users(db: Session):
    return db.query(models.DBUser).all()


def retrieve_user(db: Session, user_id: int):
    return db.query(models.DBUser).filter(models.DBUser.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.DBUser).filter(models.DBUser.username == username).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.DBUser).filter(models.DBUser.email == email).first()


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = hash_password(user.password)
    db_user = models.DBUser(
        email=user.email,
        username=user.username,
        password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict):
    expire = datetime.utcnow() + timedelta(days=30)
    data.update({"exp": expire})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def login_user(db: Session, user: schemas.UserLogin) -> schemas.UserTokenResponse:
    user_to_login = (
        db.query(models.DBUser).filter(models.DBUser.email == user.email).first()
    )
    if not user_to_login or not verify_password(user.password, user_to_login.password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.email})

    return schemas.UserTokenResponse(
        access_token=access_token, refresh_token=refresh_token
    )


def get_all_posts(db: Session):
    return db.query(models.DBPost).all()


def get_user_model(access_token: str, db: Session):
    payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
    user_email = payload.get("sub")
    user_model = db.query(models.DBUser).filter(models.DBUser.email == user_email).first()
    return user_model


def create_post(db: Session, access_token, post: schemas.PostCreate):
    user_id = (get_user_model(access_token=access_token, db=db)).id
    new_post = models.DBPost(
        topic=post.topic,
        content=post.content,
        created_at=post.created_at,
        user_id=user_id,
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


def my_profile(access_token: str, user: schemas.UserEdit, db: Session):
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")

        if user_email is None:
            raise HTTPException(
                status_code=403, detail="Invalid token or user not found"
            )

        found_user = (
            db.query(models.DBUser).filter(models.DBUser.email == user_email).first()
        )

        if found_user is None:
            raise HTTPException(status_code=404, detail="User not found")

        found_user.username = user.username
        found_user.email = user.email

        db.commit()
        db.refresh(found_user)

        return found_user

    except JWTError:
        raise HTTPException(status_code=403, detail="Could not validate credentials")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def change_password(access_token, password: schemas.UserPasswordEdit, db: Session):
    user = get_user_model(access_token=access_token, db=db)
    if verify_password(password.old_password, user.password) and user:
        new_hashed_password = hash_password(password.new_password)
        user.password = new_hashed_password
        db.commit()
        db.refresh(user)
        return True
    return False


def is_authenticated(access_token: str, db: Session):
    if not access_token:
        return False

    try:
        user_data = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = user_data.get("sub")

        if not user_email:
            return False

        user = db.query(models.DBUser).filter(models.DBUser.email == user_email).first()
        return user is not None

    except jwt.ExpiredSignatureError:
        return False
    except jwt.PyJWTError:
        return False

