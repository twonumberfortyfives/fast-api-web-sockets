import httpx
from celery import shared_task
from fastapi import HTTPException


@shared_task
def print_message(message):
    print(f"Message: {message}")
