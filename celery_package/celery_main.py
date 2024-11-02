import os

import httpx
from celery import Celery
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

celery = Celery(
    __name__,
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND")
)
celery.conf.timezone = 'UTC'


@celery.task
def add(x, y):
    return x + y


@celery.task
def create_posts():
    try:
        print("Starting create_posts task...")
        with httpx.Client() as client:
            response = client.post("http://web:8000/api/admin-make-posts")
            if response.status_code == 200:
                print("Posts have been published successfully.")
                return {"message": "Posts have been published."}
            else:
                print(f"Error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail="Error occurred.")
    except Exception as e:
        print(f"Exception in create_posts: {e}")
        raise e


# celery.conf.beat_schedule = {
#     "add_every_minute": {
#         "task": f"celery_package.celery_main.create_posts",
#         "schedule": 5.0,
#     },
# }
