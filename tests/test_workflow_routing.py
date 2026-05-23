from app.agents.routing import (
    route_after_approval,
    route_after_classify,
    route_after_generate,
)


def test_route_classify_spam_to_logger():
    assert route_after_classify({"is_spam": True}) == "logger"


def test_route_classify_non_spam_to_retriever():
    assert route_after_classify({"is_spam": False}) == "retriever"


def test_route_classify_missing_defaults_to_retriever():
    assert route_after_classify({}) == "retriever"


def test_route_approval_approved_to_sender():
    assert route_after_approval({"approval_status": "approved"}) == "sender"


def test_route_approval_rejected_to_logger():
    assert route_after_approval({"approval_status": "rejected"}) == "logger"


def test_route_approval_missing_to_logger():
    assert route_after_approval({}) == "logger"


def test_route_generate_auto_approve_to_sender():
    assert route_after_generate({"auto_approve": True}) == "sender"


def test_route_generate_no_auto_approve_to_gate():
    assert route_after_generate({"auto_approve": False}) == "approval_gate"
    assert route_after_generate({}) == "approval_gate"
