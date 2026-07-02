from celery import Celery
import os 

celery_app = Celery(
    "subscription_manager",
    broker=os.getenv("REDIS_URL","redis://redis:6379/0"),
    backend=os.getenv("REDIS_URL","redis://redis:6379/0"),
    include=[
        "app.tasks.renewal_tasks",
        "app.tasks.cancel_tasks",
        "app.tasks.email_tasks"
    ]
)