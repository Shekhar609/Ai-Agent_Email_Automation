from typing import Literal
from uuid import UUID

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.agents.llm import get_llm
from app.agents.prompts import RESPONSE_GENERATOR_SYSTEM
from app.agents.state import WorkflowState
from app.core.logging import get_logger
from app.db.models import Draft, User
from app.db.session import AsyncSessionLocal

logger = get_logger(__name__)


class DraftSpec(BaseModel):
    subject: str
    body: str
    tone: Literal["professional", "friendly", "sales", "technical"]
    confidence: float = Field(ge=0.0, le=1.0)


async def generate_response(state: WorkflowState) -> dict:
    email = state.get("email", {})
    context = state.get("retrieved_context") or []
    context_str = (
        "\n---\n".join((c.get("text") or "")[:250] for c in context) or "(no prior context)"
    )

    user_msg = (
        f"Original email:\n"
        f"From: {email.get('sender', '')}\n"
        f"Subject: {email.get('subject') or '(no subject)'}\n"
        f"Category: {state.get('category')}\n"
        f"Urgency: {state.get('urgency')}\n"
        f"Intent: {state.get('intent')}\n\n"
        f"Body:\n{(email.get('body_plain') or '')[:1500]}\n\n"
        f"---\nRelevant past emails:\n{context_str}\n"
    )

    structured = get_llm(temperature=0.4, max_tokens=1024).with_structured_output(DraftSpec)
    result: DraftSpec = await structured.ainvoke(
        [
            SystemMessage(content=RESPONSE_GENERATOR_SYSTEM),
            HumanMessage(content=user_msg),
        ]
    )

    async with AsyncSessionLocal() as db:
        user = await db.get(User, UUID(state["user_id"]))
        auto_approve = bool(
            user
            and user.auto_send_enabled
            and result.confidence >= user.auto_send_threshold
        )

        draft = Draft(
            user_id=UUID(state["user_id"]),
            email_id=UUID(state["email_id"]),
            subject=result.subject,
            body=result.body,
            tone=result.tone,
            confidence_score=result.confidence,
            status="approved" if auto_approve else "pending_approval",
            approved=auto_approve,
        )
        db.add(draft)
        await db.commit()
        await db.refresh(draft)
        draft_id = str(draft.id)

    logger.info(
        "workflow.response_generator.done",
        email_id=state["email_id"],
        draft_id=draft_id,
        confidence=result.confidence,
        tone=result.tone,
        auto_approve=auto_approve,
    )

    return {
        "draft_id": draft_id,
        "draft_subject": result.subject,
        "draft_body": result.body,
        "tone": result.tone,
        "confidence_score": result.confidence,
        "auto_approve": auto_approve,
        "approval_status": "auto_approved" if auto_approve else None,
    }
