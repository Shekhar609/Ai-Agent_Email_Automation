from app.agents.state import WorkflowState


def route_after_classify(state: WorkflowState) -> str:
    return "logger" if state.get("is_spam") else "retriever"


def route_after_generate(state: WorkflowState) -> str:
    """If user has auto-send on and confidence cleared the threshold,
    skip the approval interrupt and go straight to sender."""
    return "sender" if state.get("auto_approve") else "approval_gate"


def route_after_approval(state: WorkflowState) -> str:
    return "sender" if state.get("approval_status") == "approved" else "logger"
