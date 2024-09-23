import jwt
from fastapi import Depends, Request, HTTPException
from sqlalchemy.orm import Session

from crud import SECRET_KEY, ALGORITHM
from db import models
from db.engine import SessionLocal
from db.models import Role


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(request: Request, db: Session = Depends(get_db)):
    access_token = request.cookies.get('access_token')
    user_data = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
    user_email = user_data.get("sub")
    user = db.query(models.DBUser).filter(models.DBUser.email == user_email).first()
    return user


def require_role(required_role: Role):
    def role_checker(current_user: models.DBUser = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=403,
                detail="You are not allowed to perform this action",
            )
        return current_user
    return role_checker
