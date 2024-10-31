import os
from celery import Celery
from dotenv import load_dotenv
from celery_tasks import print_message

load_dotenv()

celery = Celery(
    __name__,
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND")
)

celery.conf.beat_schedule = {
    'print-every-10-seconds': {
        'task': f'{print_message}',  # Reference to the task
        'schedule': 10.0,  # Every 10 seconds
        'args': ('Hello from Celery!',)
    },
}

celery.conf.timezone = 'UTC'
