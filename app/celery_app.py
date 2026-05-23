from celery import Celery
from celery.schedules import schedule

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "email_automation",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.email_sync",
        "app.tasks.followup",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=60,
    task_default_max_retries=3,
    result_expires=3600 * 24,
)

celery_app.conf.beat_schedule = {
    "sync-all-inboxes": {
        "task": "email.sync_all_inboxes",
        "schedule": schedule(run_every=300),  # every 5 min
    },
    "scan-recent-replies-for-followups": {
        "task": "followup.scan_recent_replies",
        "schedule": schedule(run_every=1800),  # every 30 min
    },
    "process-due-followups": {
        "task": "followup.process_due",
        "schedule": schedule(run_every=600),  # every 10 min
    },
}
