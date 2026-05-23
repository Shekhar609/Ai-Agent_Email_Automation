import asyncio
from typing import Any

from langgraph.graph import END, StateGraph

from app.agents.nodes.approval import approval_gate
from app.agents.nodes.classifier import classify_email
from app.agents.nodes.email_reader import email_reader
from app.agents.nodes.logger import logger_node
from app.agents.nodes.response_generator import generate_response
from app.agents.nodes.retriever import retrieve_context
from app.agents.nodes.sender import sender
from app.agents.routing import (
    route_after_approval,
    route_after_classify,
    route_after_generate,
)
from app.agents.state import WorkflowState
from app.core.checkpointer import get_checkpointer
from app.core.logging import get_logger

log = get_logger(__name__)


async def _build_workflow():
    """Build and compile the StateGraph with the best-available checkpointer.

    Postgres saver is preferred (workflows survive process restarts); MemorySaver
    is the fallback. The choice is logged at startup.
    """
    g = StateGraph(WorkflowState)
    g.add_node("email_reader", email_reader)
    g.add_node("classifier", classify_email)
    g.add_node("retriever", retrieve_context)
    g.add_node("response_generator", generate_response)
    g.add_node("approval_gate", approval_gate)
    g.add_node("sender", sender)
    g.add_node("logger", logger_node)

    g.set_entry_point("email_reader")
    g.add_edge("email_reader", "classifier")
    g.add_conditional_edges(
        "classifier",
        route_after_classify,
        {"retriever": "retriever", "logger": "logger"},
    )
    g.add_edge("retriever", "response_generator")
    g.add_conditional_edges(
        "response_generator",
        route_after_generate,
        {"sender": "sender", "approval_gate": "approval_gate"},
    )
    g.add_conditional_edges(
        "approval_gate",
        route_after_approval,
        {"sender": "sender", "logger": "logger"},
    )
    g.add_edge("sender", "logger")
    g.add_edge("logger", END)

    checkpointer = await get_checkpointer()
    return g.compile(
        checkpointer=checkpointer,
        interrupt_before=["approval_gate"],
    )


_compiled: Any = None
_compile_lock = asyncio.Lock()


async def get_workflow():
    global _compiled
    if _compiled is None:
        async with _compile_lock:
            if _compiled is None:
                _compiled = await _build_workflow()
    return _compiled


def _thread_config(email_id: str) -> dict:
    return {"configurable": {"thread_id": email_id}}


def _classify_status(state: dict) -> str:
    if state.get("is_spam"):
        return "completed_spam"
    if state.get("sent_message_id"):
        return "auto_sent" if state.get("auto_approve") else "sent"
    if state.get("approval_status") == "rejected":
        return "rejected"
    if state.get("draft_id"):
        return "awaiting_approval"
    return "completed"


async def run_workflow(email_id: str, user_id: str) -> dict[str, Any]:
    wf = await get_workflow()
    config = _thread_config(email_id)
    initial: WorkflowState = {"email_id": email_id, "user_id": user_id}
    result = await wf.ainvoke(initial, config)
    log.info("workflow.run.complete", email_id=email_id, draft_id=result.get("draft_id"))
    return {
        "thread_id": email_id,
        "category": result.get("category"),
        "is_spam": bool(result.get("is_spam")),
        "draft_id": result.get("draft_id"),
        "confidence_score": result.get("confidence_score"),
        "status": _classify_status(result),
    }


async def resume_workflow(
    email_id: str, *, approved: bool, reason: str | None = None
) -> dict[str, Any]:
    wf = await get_workflow()
    config = _thread_config(email_id)
    await wf.aupdate_state(
        config,
        {
            "approval_status": "approved" if approved else "rejected",
            "rejection_reason": reason,
        },
    )
    result = await wf.ainvoke(None, config)
    log.info(
        "workflow.resume.complete",
        email_id=email_id,
        approval_status=result.get("approval_status"),
        sent_message_id=result.get("sent_message_id"),
    )
    return {
        "thread_id": email_id,
        "approval_status": result.get("approval_status"),
        "sent_message_id": result.get("sent_message_id"),
        "status": _classify_status(result),
    }
