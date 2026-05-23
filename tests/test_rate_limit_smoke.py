def test_limiter_is_configured():
    from slowapi import Limiter

    from app.core.rate_limit import limiter

    assert isinstance(limiter, Limiter)


def test_limiter_disabled_in_tests():
    # tests/conftest.py sets RATE_LIMIT_ENABLED=false; verify the limiter respects it.
    from app.core.rate_limit import limiter

    assert limiter.enabled is False
