import pytest

from app.core import oauth_state


@pytest.fixture(autouse=True)
def _reset_memory_store():
    # Force memory fallback in tests (no Redis running) and clear it between tests.
    oauth_state._memory_store.clear()
    oauth_state._redis_unavailable = True
    yield
    oauth_state._memory_store.clear()


async def test_state_round_trip_via_memory_fallback():
    state = await oauth_state.generate_state()
    assert state and len(state) > 16
    assert await oauth_state.consume_state(state) is True


async def test_state_single_use():
    state = await oauth_state.generate_state()
    assert await oauth_state.consume_state(state) is True
    # Second consume must fail — defends against replay.
    assert await oauth_state.consume_state(state) is False


async def test_unknown_state_rejected():
    assert await oauth_state.consume_state("never-issued") is False
