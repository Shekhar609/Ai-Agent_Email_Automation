"""A/B benchmark: old prompts vs. new prompts against the live LLM.

Runs the classifier and response-generator structured calls with the OLD
verbose prompts/limits, then the NEW trimmed prompts/limits, against the same
synthetic email. Reports per-call wall time and the delta.

Usage:
    .venv/Scripts/python scripts/bench_prompts_compare.py [iterations]
"""

import asyncio
import statistics
import sys
import time
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.agents.llm import get_llm
from app.agents.prompts import CLASSIFIER_SYSTEM as NEW_CLASSIFIER
from app.agents.prompts import RESPONSE_GENERATOR_SYSTEM as NEW_GENERATOR

SAMPLE_EMAIL = {
    "sender": "alex@acme.io",
    "subject": "Following up on the pilot proposal",
    "body_plain": (
        "Hi team,\n\n"
        "Wanted to check in on the pilot proposal we discussed last Thursday. "
        "Our security team had a few follow-up questions about data residency "
        "(EU-only) and SSO via Okta. If you can share a one-pager with answers, "
        "we'd like to bring this to our procurement review on Friday.\n\n"
        "Also — is the $40k annual price still on the table if we commit to 12 "
        "months up front? We'd want a 30-day out clause.\n\n"
        "Thanks,\nAlex"
    ),
}

# --- OLD prompts (verbatim from prior version) ---

OLD_CLASSIFIER = """You classify incoming emails for an automated assistant.

Choose ONE category that best fits:
- sales: prospecting, deals, pricing, demos
- support: bug reports, technical help, how-to
- hr: hiring, recruiting, internal team matters
- meeting: scheduling, calendar invites, availability
- follow-up: nudges, status checks on prior threads
- urgent: incidents, escalations, time-critical asks
- spam: unsolicited mass mail, phishing, junk
- other: anything that doesn't fit above

Also extract:
- intent: one-sentence plain description of what the sender wants
- urgency: low | medium | high | critical
- entities: named entities as a JSON object with keys like "people", "companies", "dates", "amounts" (values are lists of strings)
- confidence: your confidence in the category, 0.0 to 1.0

Be cautious about spam — never flag a real customer or internal email as spam.
"""

OLD_GENERATOR = """You draft email replies on behalf of the user.

You receive the incoming email plus classification metadata and relevant past emails from the user's history. Generate a reply that:
- Matches the category's expected register (formal for sales/support, warm for general)
- Stays concise — match the length of the incoming email, never pad
- Acknowledges every explicit ask in the sender's message
- NEVER promises things the user hasn't authorized (specific dates, prices, commitments)
- Includes a clear next step if relevant
- Omits a signature — the user appends their own

Return:
- subject: typically "Re: <original>"
- body: plain text, no signature
- tone: professional | friendly | sales | technical
- confidence: 0.0 to 1.0 — how confident you are this is the right reply
- reasoning: 1-2 sentences explaining the approach

If the email is ambiguous, hostile, or requests sensitive info (passwords, payments, legal commitments), lower the confidence and draft a careful holding response that defers to the user.
"""


class OldClassification(BaseModel):
    category: Literal["sales", "support", "hr", "meeting", "follow-up", "urgent", "spam", "other"]
    intent: str
    urgency: Literal["low", "medium", "high", "critical"]
    entities: dict[str, list[str]] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)


class OldDraftSpec(BaseModel):
    subject: str
    body: str
    tone: Literal["professional", "friendly", "sales", "technical"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str


class NewClassification(BaseModel):
    category: Literal["sales", "support", "hr", "meeting", "follow-up", "urgent", "spam", "other"]
    intent: str
    urgency: Literal["low", "medium", "high", "critical"]
    entities: dict[str, list[str]] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)


class NewDraftSpec(BaseModel):
    subject: str
    body: str
    tone: Literal["professional", "friendly", "sales", "technical"]
    confidence: float = Field(ge=0.0, le=1.0)


def _classifier_msgs(system: str, body_trunc: int) -> list:
    body = SAMPLE_EMAIL["body_plain"][:body_trunc]
    text = (
        f"From: {SAMPLE_EMAIL['sender']}\n"
        f"Subject: {SAMPLE_EMAIL['subject']}\n\n{body}"
    )
    return [SystemMessage(content=system), HumanMessage(content=text)]


def _generator_msgs(system: str, body_trunc: int) -> list:
    body = SAMPLE_EMAIL["body_plain"][:body_trunc]
    user_msg = (
        f"Original email:\n"
        f"From: {SAMPLE_EMAIL['sender']}\n"
        f"Subject: {SAMPLE_EMAIL['subject']}\n"
        f"Category: sales\nUrgency: medium\n"
        f"Intent: Prospect wants follow-up answers and pricing confirmation.\n\n"
        f"Body:\n{body}\n\n"
        f"---\nRelevant past emails:\n(no prior context)\n"
    )
    return [SystemMessage(content=system), HumanMessage(content=user_msg)]


async def _time(runner) -> float:
    t0 = time.perf_counter()
    await runner()
    return time.perf_counter() - t0


async def main(iterations: int) -> None:
    # OLD settings: max_tokens=2048, body trunc 4000 / 3000
    old_cls = get_llm(temperature=0.1, max_tokens=2048).with_structured_output(OldClassification)
    old_gen = get_llm(temperature=0.4, max_tokens=2048).with_structured_output(OldDraftSpec)
    # NEW settings: max_tokens 512/1024, body trunc 1500/1500
    new_cls = get_llm(temperature=0.1, max_tokens=512).with_structured_output(NewClassification)
    new_gen = get_llm(temperature=0.4, max_tokens=1024).with_structured_output(NewDraftSpec)

    print(f"\n--- A/B latency: OLD vs NEW prompts ({iterations} iter) ---\n")

    old_cls_t: list[float] = []
    new_cls_t: list[float] = []
    old_gen_t: list[float] = []
    new_gen_t: list[float] = []

    for i in range(iterations):
        print(f"Iter {i+1}:")
        t = await _time(lambda: old_cls.ainvoke(_classifier_msgs(OLD_CLASSIFIER, 4000)))
        old_cls_t.append(t); print(f"  OLD classify : {t*1000:7.0f} ms")
        t = await _time(lambda: new_cls.ainvoke(_classifier_msgs(NEW_CLASSIFIER, 1500)))
        new_cls_t.append(t); print(f"  NEW classify : {t*1000:7.0f} ms")
        t = await _time(lambda: old_gen.ainvoke(_generator_msgs(OLD_GENERATOR, 3000)))
        old_gen_t.append(t); print(f"  OLD generate : {t*1000:7.0f} ms")
        t = await _time(lambda: new_gen.ainvoke(_generator_msgs(NEW_GENERATOR, 1500)))
        new_gen_t.append(t); print(f"  NEW generate : {t*1000:7.0f} ms")
        print()

    def _stats(label: str, xs: list[float]) -> tuple[float, float]:
        ms = [x * 1000 for x in xs]
        mean = statistics.mean(ms)
        median = statistics.median(ms)
        print(
            f"{label:>14s}  mean={mean:7.0f} ms  median={median:7.0f} ms  "
            f"min={min(ms):7.0f} ms  max={max(ms):7.0f} ms"
        )
        return mean, median

    print("--- Summary ---")
    old_cls_mean, _ = _stats("OLD classify", old_cls_t)
    new_cls_mean, _ = _stats("NEW classify", new_cls_t)
    old_gen_mean, _ = _stats("OLD generate", old_gen_t)
    new_gen_mean, _ = _stats("NEW generate", new_gen_t)

    print()
    print(f"classify delta: {old_cls_mean - new_cls_mean:+7.0f} ms  "
          f"({(new_cls_mean/old_cls_mean - 1) * 100:+.1f}%)")
    print(f"generate delta: {old_gen_mean - new_gen_mean:+7.0f} ms  "
          f"({(new_gen_mean/old_gen_mean - 1) * 100:+.1f}%)")
    old_total = old_cls_mean + old_gen_mean
    new_total = new_cls_mean + new_gen_mean
    print(f"   total delta: {old_total - new_total:+7.0f} ms  "
          f"({(new_total/old_total - 1) * 100:+.1f}%)")


if __name__ == "__main__":
    iters = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    asyncio.run(main(iters))
