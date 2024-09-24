from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from users.routes import router as users_router
from posts.routes import router as posts_router


app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(users_router, prefix="/api", tags=["users"])
app.include_router(posts_router, prefix="/api", tags=["posts"])


@app.get("/")
async def root():
    return {"message": "Hello World"}
