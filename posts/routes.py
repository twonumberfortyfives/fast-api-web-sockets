import jwt
from fastapi import Depends, Request, APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_db
from posts import serializers, views
from users.views import SECRET_KEY, ALGORITHM

router = APIRouter()


@router.get("/get-posts", response_model=list[serializers.Post])
async def get_all_posts(db: AsyncSession = Depends(get_db)):
    return await views.get_all_posts(db)


@router.post("/create-post", response_model=serializers.Post)
async def create_post(
    request: Request, post: serializers.PostCreate, db: AsyncSession = Depends(get_db)
):
    access_token = request.cookies.get("access_token")

    if not access_token:
        raise HTTPException(status_code=403, detail="Access token is missing")

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=403, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401, detail="Token has expired. Please log in again."
        )
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=403, detail=f"Token validation error: {str(e)}")
    response = await views.create_post(db=db, access_token=access_token, post=post)
    return response


@router.patch("/edit-post/{post_id}", response_model=serializers.Post)
async def edit_post(
    post_update: serializers.PostUpdate,
    post_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    access_token = request.cookies.get("access_token")

    if not access_token:
        raise HTTPException(status_code=403, detail="Not authorized.")

    result = await views.change_post(
        post_update=post_update, post_id=post_id, access_token=access_token, db=db
    )

    return result
