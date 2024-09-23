from sqlalchemy.orm import Session
from db import models
import schemas


def get_all_users(db: Session):
    return db.query(models.DBUser).all()


def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.DBUser(
        username=user.username,
        password=user.password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
