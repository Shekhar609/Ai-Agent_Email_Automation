"""Micro-benchmark for prompt latency.

Calls the classifier and response-generator LLMs directly against a synthetic
email, skipping DB writes. Reports per-call wall time and tokens (when the
provider returns usage metadata).

Usage:
    .venv/Scripts/python scripts/bench_prompts.py [iterations]
"""

import asyncio
import statistics
import sys
import time

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm import get_llm
from app.agents.nodes.classifier import Classification
from app.agents.nodes.response_generator import DraftSpec
from app.agents.prompts import CLASSIFIER_SYSTEM, RESPONSE_GENERATOR_SYSTEM

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


def _classifier_input() -> list:
    body = (SAMPLE_EMAIL["body_plain"])[:1500]
    text = (
        f"From: {SAMPLE_EMAIL['sender']}\n"
        f"Subject: {SAMPLE_EMAIL['subject']}\n\n{body}"
    )
    return [SystemMessage(content=CLASSIFIER_SYSTEM), HumanMessage(content=text)]


def _generator_input() -> list:
    body = (SAMPLE_EMAIL["body_plain"])[:1500]
    user_msg = (
        f"Original email:\n"
        f"From: {SAMPLE_EMAIL['sender']}\n"
        f"Subject: {SAMPLE_EMAIL['subject']}\n"
        f"Category: sales\nUrgency: medium\n"
        f"Intent: Prospect wants follow-up answers and pricing confirmation.\n\n"
        f"Body:\n{body}\n\n"
        f"---\nRelevant past emails:\n(no prior context)\n"
    )
    return [SystemMessage(content=RESPONSE_GENERATOR_SYSTEM), HumanMessage(content=user_msg)]


async def _time_call(name: str, runner) -> float:
    t0 = time.perf_counter()
    result = await runner()
    dt = time.perf_counter() - t0
    preview = str(result)[:80].replace("\n", " ")
    print(f"  {name:>10s}: {dt*1000:7.0f} ms  | {preview}...")
    return dt


async def main(iterations: int) -> None:
    classifier = get_llm(temperature=0.1, max_tokens=512).with_structured_output(Classification)
    generator = get_llm(temperature=0.4, max_tokens=1024).with_structured_output(DraftSpec)

    print(f"\n--- Prompt latency benchmark ({iterations} iter) ---\n")

    cls_times: list[float] = []
    gen_times: list[float] = []

    for i in range(iterations):
        print(f"Iter {i+1}:")
        cls_times.append(await _time_call("classify", lambda: classifier.ainvoke(_classifier_input())))
        gen_times.append(await _time_call("generate", lambda: generator.ainvoke(_generator_input())))
        print()

    def _stat(label: str, xs: list[float]) -> None:
        ms = [x * 1000 for x in xs]
        print(
            f"{label:>10s}  mean={statistics.mean(ms):7.0f} ms  "
            f"median={statistics.median(ms):7.0f} ms  "
            f"min={min(ms):7.0f} ms  max={max(ms):7.0f} ms"
        )

    print("--- Summary ---")
    _stat("classify", cls_times)
    _stat("generate", gen_times)
    total = [c + g for c, g in zip(cls_times, gen_times)]
    _stat("total", total)


if __name__ == "__main__":
    iters = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    asyncio.run(main(iters))
