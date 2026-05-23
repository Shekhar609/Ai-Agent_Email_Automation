from uuid import UUID

from app.agents.state import WorkflowState
from app.core.logging import get_logger
from app.core.security import decrypt
from app.db.models import Draft, Email, User
from app.db.session import AsyncSessionLocal
from app.services import gmail

logger = get_logger(__name__)


async def sender(state: WorkflowState) -> dict:
    draft_id = state.get("draft_id")
    if not draft_id:
        logger.warning("workflow.sender.no_draft", email_id=state.get("email_id"))
        return {"sent_message_id": None}

    async with AsyncSessionLocal() as db:
        draft = await db.get(Draft, UUID(draft_id))
        email = await db.get(Email, UUID(state["email_id"]))
        user = await db.get(User, UUID(state["user_id"]))

        if draft is None or email is None or user is None:
            raise RuntimeError("missing draft, email, or user during send")
        if not user.google_refresh_token:
            raise RuntimeError("user has no google_refresh_token; cannot send")

        refresh = decrypt(user.google_refresh_token)
        subject = draft.subject or (f"Re: {email.subject}" if email.subject else "Re:")

        result = await gmail.send_message(
            refresh,
            to=email.sender,
            subject=subject,
            body=draft.body,
            thread_id=email.thread_id,
        )
        sent_id = result.get("id")

        draft.sent = True
        draft.status = "sent"
        await db.commit()

    logger.info(
        "workflow.sender.done",
        email_id=state["email_id"],
        draft_id=draft_id,
        sent_message_id=sent_id,
    )
    return {"sent_message_id": sent_id}
