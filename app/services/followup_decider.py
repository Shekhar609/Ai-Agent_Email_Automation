from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.agents.llm import get_llm

FOLLOWUP_DECIDER_SYSTEM = """You decide whether an email needs a follow-up if no reply is received.

Given an original email and the user's reply already sent, return:
- needs_followup: should we follow up if there's no response?
- days_until: how many days from now to send the follow-up (1-30)
- reason: one sentence explaining the decision

Rules of thumb:
- Sales/pricing/demos: usually yes, 2-5 days
- Support/incidents: usually yes, 1-3 days
- Casual/internal/already-answered: usually no
- Auto-replies, spam, no actionable ask: no

Bias toward NOT following up for low-stakes or already-resolved threads.
"""

FOLLOWUP_WRITER_SYSTEM = """Write a brief, polite follow-up email.

You receive the original incoming email and the user's prior reply. Write a follow-up that:
- Is 3-5 sentences max
- References the prior message naturally ("Just wanted to circle back on...")
- Restates the ask or expected next step
- Is warm but not pushy
- Has no signature (the user appends their own)

Return ONLY the email body — no subject, no headers.
"""


class FollowUpDecision(BaseModel):
    needs_followup: bool
    days_until: int = Field(default=3, ge=1, le=30)
    reason: str = ""


async def decide_followup(
    original_email: dict,
    sent_reply: dict,
) -> FollowUpDecision:
    user_msg = (
        f"Original email from sender:\n"
        f"From: {original_email.get('sender', '')}\n"
        f"Subject: {original_email.get('subject') or '(no subject)'}\n"
        f"Body: {(original_email.get('body_plain') or '')[:1500]}\n\n"
        f"User's reply (already sent):\n"
        f"Subject: {sent_reply.get('subject') or ''}\n"
        f"Body: {(sent_reply.get('body') or '')[:1500]}\n"
    )
    structured = get_llm(temperature=0.2).with_structured_output(FollowUpDecision)
    return await structured.ainvoke(
        [
            SystemMessage(content=FOLLOWUP_DECIDER_SYSTEM),
            HumanMessage(content=user_msg),
        ]
    )


async def write_followup_body(
    original_email: dict,
    sent_reply: dict,
    reason: str | None,
) -> str:
    user_msg = (
        f"Original email from sender:\n"
        f"From: {original_email.get('sender', '')}\n"
        f"Subject: {original_email.get('subject') or '(no subject)'}\n"
        f"Body: {(original_email.get('body_plain') or '')[:1500]}\n\n"
        f"User's prior reply already sent:\n"
        f"Subject: {sent_reply.get('subject') or ''}\n"
        f"Body: {(sent_reply.get('body') or '')[:1500]}\n\n"
        f"Reason for following up: {reason or 'no response received yet'}\n"
    )
    msg = await get_llm(temperature=0.3).ainvoke(
        [
            SystemMessage(content=FOLLOWUP_WRITER_SYSTEM),
            HumanMessage(content=user_msg),
        ]
    )
    return msg.content if isinstance(msg.content, str) else str(msg.content)
