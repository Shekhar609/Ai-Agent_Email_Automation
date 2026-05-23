from uuid import UUID

from app.agents.state import WorkflowState
from app.core.logging import get_logger
from app.db.models import ActivityLog
from app.db.session import AsyncSessionLocal

log = get_logger(__name__)


async def logger_node(state: WorkflowState) -> dict:
    async with AsyncSessionLocal() as db:
        entry = ActivityLog(
            user_id=UUID(state["user_id"]),
            email_id=UUID(state["email_id"]) if state.get("email_id") else None,
            draft_id=UUID(state["draft_id"]) if state.get("draft_id") else None,
            category=state.get("category"),
            approval_status=state.get("approval_status"),
            sent=bool(state.get("sent_message_id")),
            error=state.get("error"),
            payload={
                "is_spam": state.get("is_spam"),
                "urgency": state.get("urgency"),
                "intent": state.get("intent"),
                "tone": state.get("tone"),
                "confidence_score": state.get("confidence_score"),
                "sent_message_id": state.get("sent_message_id"),
                "rejection_reason": state.get("rejection_reason"),
            },
        )
        db.add(entry)
        await db.commit()

    log.info(
        "workflow.logger.done",
        email_id=state.get("email_id"),
        category=state.get("category"),
        approval_status=state.get("approval_status"),
        sent=bool(state.get("sent_message_id")),
    )
    return {}
