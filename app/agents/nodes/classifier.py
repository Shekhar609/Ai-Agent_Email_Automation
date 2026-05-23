from typing import Literal
from uuid import UUID

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.agents.llm import get_llm
from app.agents.prompts import CLASSIFIER_SYSTEM
from app.agents.state import WorkflowState
from app.core.logging import get_logger
from app.db.models import Email
from app.db.session import AsyncSessionLocal

logger = get_logger(__name__)


class Classification(BaseModel):
    category: Literal["sales", "support", "hr", "meeting", "follow-up", "urgent", "spam", "other"]
    intent: str = Field(description="One-sentence summary of what the sender wants")
    urgency: Literal["low", "medium", "high", "critical"]
    entities: dict[str, list[str]] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)


async def classify_email(state: WorkflowState) -> dict:
    email = state["email"]
    body = (email.get("body_plain") or "")[:4000]
    text = (
        f"From: {email.get('sender', '')}\n"
        f"Subject: {email.get('subject') or '(no subject)'}\n\n"
        f"{body}"
    )

    structured = get_llm(temperature=0.1).with_structured_output(Classification)
    result: Classification = await structured.ainvoke(
        [
            SystemMessage(content=CLASSIFIER_SYSTEM),
            HumanMessage(content=text),
        ]
    )

    async with AsyncSessionLocal() as db:
        email_obj = await db.get(Email, UUID(state["email_id"]))
        if email_obj is not None:
            email_obj.category = result.category
            email_obj.intent = result.intent
            email_obj.urgency = result.urgency
            email_obj.entities = result.entities
            await db.commit()

    logger.info(
        "workflow.classifier.done",
        email_id=state["email_id"],
        category=result.category,
        urgency=result.urgency,
        confidence=result.confidence,
    )

    return {
        "category": result.category,
        "intent": result.intent,
        "urgency": result.urgency,
        "entities": result.entities,
        "is_spam": result.category == "spam",
    }
