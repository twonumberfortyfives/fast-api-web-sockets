from sqlalchemy.orm import Session
from db import models
import schemas


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


def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.DBUser(
        email=user.email,
        username=user.username,
        password=user.password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

