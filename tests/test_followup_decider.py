from app.services.followup_decider import FollowUpDecision


def test_followup_decision_defaults():
    d = FollowUpDecision(needs_followup=True)
    assert d.needs_followup is True
    assert d.days_until == 3
    assert d.reason == ""


def test_followup_decision_clamps_days():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        FollowUpDecision(needs_followup=True, days_until=0)
    with pytest.raises(ValidationError):
        FollowUpDecision(needs_followup=True, days_until=31)


def test_followup_decision_serializes():
    d = FollowUpDecision(needs_followup=True, days_until=5, reason="sales prospect")
    assert d.model_dump() == {
        "needs_followup": True,
        "days_until": 5,
        "reason": "sales prospect",
    }
