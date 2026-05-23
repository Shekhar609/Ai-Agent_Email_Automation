from uuid import UUID

from app.agents.state import WorkflowState
from app.core.logging import get_logger
from app.db.models import Email
from app.db.session import AsyncSessionLocal

logger = get_logger(__name__)


async def email_reader(state: WorkflowState) -> dict:
    async with AsyncSessionLocal() as db:
        email = await db.get(Email, UUID(state["email_id"]))
        if email is None:
            raise ValueError(f"email {state['email_id']} not found")

        snapshot = {
            "id": str(email.id),
            "sender": email.sender,
            "recipient": email.recipient,
            "subject": email.subject,
            "body_plain": email.body_plain,
            "thread_id": email.thread_id,
            "received_at": email.received_at.isoformat() if email.received_at else None,
        }

    logger.info("workflow.email_reader.loaded", email_id=state["email_id"])
    return {"email": snapshot}
