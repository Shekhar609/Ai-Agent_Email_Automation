import asyncio
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
from app.vectorstore import chroma_client

logger = get_logger(__name__)


class Classification(BaseModel):
    category: Literal["sales", "support", "hr", "meeting", "follow-up", "urgent", "spam", "other"]
    intent: str = Field(description="One-sentence summary of what the sender wants")
    urgency: Literal["low", "medium", "high", "critical"]
    entities: dict[str, list[str]] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)


async def _retrieve(user_id: str, query: str) -> list[dict]:
    if not query:
        return []
    try:
        return await asyncio.to_thread(
            chroma_client.search, user_id=user_id, query=query, n_results=3
        )
    except Exception as exc:
        logger.warning("workflow.retriever.failed", error=str(exc))
        return []


async def classify_email(state: WorkflowState) -> dict:
    email = state["email"]
    body = (email.get("body_plain") or "")[:1500]
    text = (
        f"From: {email.get('sender', '')}\n"
        f"Subject: {email.get('subject') or '(no subject)'}\n\n"
        f"{body}"
    )

    structured = get_llm(temperature=0.1, max_tokens=512).with_structured_output(Classification)
    # Kick off retrieval in parallel with the classifier LLM call — they don't
    # depend on each other and this overlaps a Chroma round-trip with the LLM call.
    retrieval_query = f"{email.get('subject') or ''}\n{(email.get('body_plain') or '')[:300]}".strip()
    classify_task = structured.ainvoke(
        [
            SystemMessage(content=CLASSIFIER_SYSTEM),
            HumanMessage(content=text),
        ]
    )
    retrieve_task = _retrieve(state["user_id"], retrieval_query)
    result, retrieved = await asyncio.gather(classify_task, retrieve_task)

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
        "retrieved_context": retrieved,
    }
