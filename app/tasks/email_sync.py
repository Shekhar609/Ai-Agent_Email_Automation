from sqlalchemy import select

from app.celery_app import celery_app
from app.core.logging import get_logger
from app.db.models import User
from app.services.email_sync import sync_inbox
from app.tasks.db import TaskSessionLocal, run_async

logger = get_logger(__name__)


@celery_app.task(name="email.sync_all_inboxes", bind=True, max_retries=2)
def sync_all_inboxes_task(self) -> dict:
    try:
        return run_async(_sync_all_inboxes())
    except Exception as exc:
        logger.exception("task.sync_all_inboxes.failed", error=str(exc))
        raise self.retry(exc=exc, countdown=60) from exc


async def _sync_all_inboxes() -> dict:
    async with TaskSessionLocal() as db:
        users = (
            await db.scalars(
                select(User).where(
                    User.is_active.is_(True),
                    User.google_refresh_token.is_not(None),
                )
            )
        ).all()

        report: dict[str, dict] = {}
        for user in users:
            try:
                result = await sync_inbox(db, user, max_results=20)
                report[str(user.id)] = result
            except Exception as exc:
                logger.warning(
                    "task.sync_inbox.user_failed",
                    user_id=str(user.id),
                    error=str(exc),
                )
                report[str(user.id)] = {"error": str(exc)}

    logger.info("task.sync_all_inboxes.done", users=len(report))
    return {"users_synced": len(report), "results": report}


@celery_app.task(name="email.sync_user_inbox", bind=True, max_retries=2)
def sync_user_inbox_task(self, user_id: str, max_results: int = 20) -> dict:
    try:
        return run_async(_sync_user_inbox(user_id, max_results))
    except Exception as exc:
        logger.exception("task.sync_user_inbox.failed", user_id=user_id, error=str(exc))
        raise self.retry(exc=exc, countdown=60) from exc


async def _sync_user_inbox(user_id: str, max_results: int) -> dict:
    from uuid import UUID

    async with TaskSessionLocal() as db:
        user = await db.get(User, UUID(user_id))
        if user is None:
            raise ValueError(f"user {user_id} not found")
        return await sync_inbox(db, user, max_results=max_results)
