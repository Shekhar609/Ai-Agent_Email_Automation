from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, select

from app.celery_app import celery_app
from app.core.logging import get_logger
from app.db.models import Draft, Email, FollowUp, User
from app.services.followup_decider import decide_followup, write_followup_body
from app.tasks.db import TaskSessionLocal, run_async

logger = get_logger(__name__)


@celery_app.task(name="followup.scan_recent_replies", bind=True, max_retries=2)
def scan_recent_replies_task(self) -> dict:
    try:
        return run_async(_scan_recent_replies())
    except Exception as exc:
        logger.exception("task.followup_scan.failed", error=str(exc))
        raise self.retry(exc=exc, countdown=120) from exc


async def _scan_recent_replies() -> dict:
    """For drafts sent in the last 24h that don't yet have a follow-up record,
    ask the LLM whether one is warranted and create a FollowUp row if so."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    decided = 0
    scheduled = 0

    async with TaskSessionLocal() as db:
        # Sent drafts with no follow-up yet
        existing_email_ids_stmt = select(FollowUp.email_id).where(
            FollowUp.email_id.is_not(None)
        )
        stmt = (
            select(Draft, Email)
            .join(Email, Draft.email_id == Email.id)
            .where(
                and_(
                    Draft.sent.is_(True),
                    Draft.updated_at >= cutoff,
                    Draft.email_id.not_in(existing_email_ids_stmt),
                )
            )
        )
        rows = (await db.execute(stmt)).all()

        for draft, email in rows:
            decided += 1
            try:
                decision = await decide_followup(
                    original_email={
                        "sender": email.sender,
                        "subject": email.subject,
                        "body_plain": email.body_plain,
                    },
                    sent_reply={
                        "subject": draft.subject,
                        "body": draft.body,
                    },
                )
            except Exception as exc:
                logger.warning(
                    "task.followup_scan.decide_failed",
                    draft_id=str(draft.id),
                    error=str(exc),
                )
                continue

            if not decision.needs_followup:
                continue

            f = FollowUp(
                user_id=draft.user_id,
                email_id=email.id,
                thread_id=email.thread_id,
                scheduled_for=datetime.now(timezone.utc)
                + timedelta(days=decision.days_until),
                reason=decision.reason,
                status="pending",
            )
            db.add(f)
            scheduled += 1

        await db.commit()

    logger.info(
        "task.followup_scan.done",
        decided=decided,
        scheduled=scheduled,
    )
    return {"decided": decided, "scheduled": scheduled}


@celery_app.task(name="followup.process_due", bind=True, max_retries=2)
def process_due_followups_task(self) -> dict:
    try:
        return run_async(_process_due_followups())
    except Exception as exc:
        logger.exception("task.process_due.failed", error=str(exc))
        raise self.retry(exc=exc, countdown=120) from exc


async def _process_due_followups() -> dict:
    """For each pending follow-up whose scheduled_for has passed, generate a
    draft (always pending_approval — user reviews follow-ups manually for now).
    """
    now = datetime.now(timezone.utc)
    processed = 0
    failed = 0

    async with TaskSessionLocal() as db:
        due = (
            await db.scalars(
                select(FollowUp).where(
                    FollowUp.status == "pending",
                    FollowUp.scheduled_for <= now,
                )
            )
        ).all()

        for f in due:
            try:
                f.status = "processing"
                await db.commit()

                email = await db.get(Email, f.email_id) if f.email_id else None
                if email is None:
                    raise ValueError(f"followup {f.id} has no email")

                # Find the prior reply (most recent sent draft for this email)
                prior_draft = await db.scalar(
                    select(Draft)
                    .where(Draft.email_id == email.id, Draft.sent.is_(True))
                    .order_by(Draft.updated_at.desc())
                    .limit(1)
                )
                if prior_draft is None:
                    raise ValueError(f"followup {f.id}: no prior sent draft")

                body = await write_followup_body(
                    original_email={
                        "sender": email.sender,
                        "subject": email.subject,
                        "body_plain": email.body_plain,
                    },
                    sent_reply={
                        "subject": prior_draft.subject,
                        "body": prior_draft.body,
                    },
                    reason=f.reason,
                )

                followup_draft = Draft(
                    user_id=f.user_id,
                    email_id=email.id,
                    subject=f"Re: {email.subject}" if email.subject else "Following up",
                    body=body,
                    tone="professional",
                    confidence_score=0.7,
                    status="pending_approval",
                )
                db.add(followup_draft)
                await db.flush()
                f.draft_id = followup_draft.id
                f.status = "completed"
                f.completed_at = datetime.now(timezone.utc)
                await db.commit()
                processed += 1

            except Exception as exc:
                logger.warning(
                    "task.process_due.failed_one",
                    followup_id=str(f.id),
                    error=str(exc),
                )
                f.status = "failed"
                f.error = str(exc)[:1000]
                await db.commit()
                failed += 1

    logger.info("task.process_due.done", processed=processed, failed=failed)
    return {"processed": processed, "failed": failed}


@celery_app.task(name="followup.run_one", bind=True, max_retries=2)
def run_one_followup_task(self, followup_id: str) -> dict:
    try:
        return run_async(_run_one_followup(followup_id))
    except Exception as exc:
        logger.exception("task.run_one.failed", followup_id=followup_id, error=str(exc))
        raise self.retry(exc=exc, countdown=60) from exc


async def _run_one_followup(followup_id: str) -> dict:
    async with TaskSessionLocal() as db:
        f = await db.get(FollowUp, UUID(followup_id))
        if f is None:
            return {"status": "not_found"}
        if f.status != "pending":
            return {"status": f.status}
        # Force the scheduled time so process_due picks it up
        f.scheduled_for = datetime.now(timezone.utc)
        await db.commit()
    # Reuse the batch processor
    return await _process_due_followups()
