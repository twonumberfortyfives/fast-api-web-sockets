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
