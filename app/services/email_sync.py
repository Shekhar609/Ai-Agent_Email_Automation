import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import decrypt
from app.db.models import Email, User
from app.services import gmail
from app.vectorstore import chroma_client

logger = get_logger(__name__)


async def sync_inbox(
    db: AsyncSession,
    user: User,
    *,
    max_results: int = 20,
) -> dict[str, int]:
    if not user.google_refresh_token:
        raise ValueError("user has no google_refresh_token; complete OAuth first")
    refresh_token = decrypt(user.google_refresh_token)

    message_ids = await gmail.list_recent_message_ids(refresh_token, max_results=max_results)
    if not message_ids:
        return {"fetched": 0, "created": 0, "skipped": 0}

    existing_rows = await db.scalars(
        select(Email.message_id).where(
            Email.user_id == user.id,
            Email.message_id.in_(message_ids),
        )
    )
    existing_ids = set(existing_rows.all())
    new_ids = [mid for mid in message_ids if mid not in existing_ids]

    created = 0
    for mid in new_ids:
        raw = await gmail.fetch_message(refresh_token, mid)
        parsed = gmail.parse_message(raw)
        email_obj = Email(user_id=user.id, **parsed)
        db.add(email_obj)
        await db.flush()  # populate email_obj.id

        text = (
            f"Subject: {parsed.get('subject') or ''}\n\n"
            f"{parsed.get('body_plain') or ''}"
        )
        try:
            await asyncio.to_thread(
                chroma_client.upsert_email,
                email_id=str(email_obj.id),
                user_id=str(user.id),
                text=text,
                metadata={
                    "sender": parsed.get("sender") or "",
                    "subject": parsed.get("subject") or "",
                    "thread_id": parsed.get("thread_id") or "",
                },
            )
        except Exception as exc:
            # Don't fail the whole sync on a vector-store hiccup — log and continue.
            logger.warning(
                "chroma.upsert_failed",
                email_id=str(email_obj.id),
                error=str(exc),
            )
        created += 1

    await db.commit()
    logger.info(
        "email_sync.complete",
        user_id=str(user.id),
        fetched=len(message_ids),
        created=created,
        skipped=len(existing_ids),
    )
    return {
        "fetched": len(message_ids),
        "created": created,
        "skipped": len(existing_ids),
    }
