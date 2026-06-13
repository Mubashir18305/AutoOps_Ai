import os
from celery import Celery

# Initialize Celery app
# In production, use Redis or RabbitMQ as the broker
# e.g., broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
celery_app = Celery(
    "ai_os_triggers",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1"
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Example of Celery Beat schedule for recurring agent workflows
celery_app.conf.beat_schedule = {
    "weekly-competitor-research": {
        "task": "src.triggers.tasks.run_scheduled_research",
        "schedule": 604800.0, # Every 7 days (in seconds)
        # Or using crontab:
        # "schedule": crontab(day_of_week='friday', hour=17, minute=0),
    },
    "daily-crm-sync": {
        "task": "src.triggers.tasks.run_scheduled_crm_sync",
        "schedule": 86400.0, # Every 24 hours
    }
}
