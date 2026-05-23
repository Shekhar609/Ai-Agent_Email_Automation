from app.agents.state import WorkflowState
from app.core.logging import get_logger

logger = get_logger(__name__)


async def approval_gate(state: WorkflowState) -> dict:
    """Pass-through node. Workflow is configured to `interrupt_before` this node;
    when resumed, `state["approval_status"]` has been set by the API layer and
    the conditional edge routes accordingly."""
    logger.info(
        "workflow.approval_gate.passing",
        email_id=state.get("email_id"),
        draft_id=state.get("draft_id"),
        approval_status=state.get("approval_status"),
    )
    return {}
