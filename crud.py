from passlib.context import CryptContext
from sqlalchemy.orm import Session
from db import models
import schemas


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_all_users(db: Session):
    return db.query(models.DBUser).all()


def get_user_by_username(db: Session, username: str):
    return (
        db.query(models.DBUser).filter(models.DBUser.username == username).first()
    )


def get_user_by_email(db: Session, email: str):
    return (
        db.query(models.DBUser).filter(models.DBUser.email == email).first()
    )


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

