from typing import Literal, TypedDict


class WorkflowState(TypedDict, total=False):
    # Input
    email_id: str
    user_id: str

    # email_reader output
    email: dict

    # classifier output
    category: str
    intent: str
    urgency: str
    entities: dict
    is_spam: bool

    # retriever output
    retrieved_context: list[dict]

    # response_generator output
    draft_id: str
    draft_subject: str
    draft_body: str
    tone: str
    confidence_score: float
    auto_approve: bool

    # approval
    approval_status: Literal["pending", "approved", "rejected", "auto_approved"]
    rejection_reason: str | None

    # sender
    sent_message_id: str | None

    # error tracking
    error: str | None
