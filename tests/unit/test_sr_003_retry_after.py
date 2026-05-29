"""Tests for SR-003: Honor Retry-After header on 429.

GREEN (was RED phase; retry_after attribute and wait function implemented).
"""

from __future__ import annotations

import pytest
from tenacity import RetryCallState

from ado_odata_async.exceptions import RateLimitError, TransientError

# ── AC-1: RateLimitError stores retry_after attribute ─────────────


def test_ac1_rate_limit_error_stores_retry_after() -> None:
    """AC-1: RateLimitError accepts retry_after and exposes it as attribute."""
    exc = RateLimitError("HTTP 429: Rate limit. Retry-After: 60s", retry_after=60.0)

    assert exc.retry_after == 60.0
    assert "Rate limit" in str(exc)


def test_ac1_rate_limit_error_default_retry_after_none() -> None:
    """AC-1: RateLimitError without retry_after defaults to None."""
    exc = RateLimitError("HTTP 429: Rate limit")
    assert exc.retry_after is None


# ── AC-2: Custom wait function reads retry_after ──────────────────


def _state_with_exception(exc: BaseException) -> RetryCallState:
    """Build a RetryCallState whose outcome is the given exception."""
    from tenacity import Future, RetryCallState

    state = RetryCallState(None, None, (), {})
    fut = Future(attempt_number=1)
    fut.set_exception(exc)
    state.outcome = fut
    return state


def test_ac2_wait_fn_reads_retry_after() -> None:
    """AC-2: Custom wait function returns >= retry_after when RateLimitError has it."""

    from ado_odata_async.retry import _make_wait

    wait_fn = _make_wait()
    state = _state_with_exception(RateLimitError("Rate limited", retry_after=60.0))
    wait = wait_fn(state)
    assert wait >= 60.0, f"Expected wait >= 60.0, got {wait}"


# ── AC-3: Custom wait function falls back to jitter for non-retry-after ──


def test_ac3_wait_fn_fallback_jitter() -> None:
    """AC-3: Custom wait returns 0.5-10.0s for generic TransientError."""
    from ado_odata_async.retry import _make_wait

    wait_fn = _make_wait()
    state = _state_with_exception(TransientError("Service Unavailable"))
    wait = wait_fn(state)
    assert 0.5 <= wait <= 10.0, f"Expected 0.5-10.0s, got {wait}"


# ── AC-4: parse_response passes Retry-After from 429 ──────────────


@pytest.mark.asyncio
async def test_ac4_parse_response_passes_retry_after() -> None:
    """AC-4: parse_response raises RateLimitError with retry_after from header."""
    from unittest.mock import MagicMock

    from ado_odata_async._http import parse_response

    # Mock a 429 response with Retry-After: 30
    resp = MagicMock(spec=[])
    resp.status = 429
    resp.headers = {"Retry-After": "30"}
    resp.content_type = "application/json"

    with pytest.raises(RateLimitError) as exc_info:
        await parse_response(resp)

    assert exc_info.value.retry_after == 30.0


# ── AC-5: RateLimitError without retry_after falls back to jitter ─


def test_ac5_no_retry_after_fallback() -> None:
    """AC-5: RateLimitError without retry_after: exc.retry_after is None, wait falls back."""
    from ado_odata_async.retry import _make_wait

    # Create RateLimitError without retry_after
    exc = RateLimitError("HTTP 429: Rate limit")
    assert exc.retry_after is None

    wait_fn = _make_wait()
    state = _state_with_exception(RateLimitError("HTTP 429: Rate limit"))
    wait = wait_fn(state)
    assert 0.5 <= wait <= 10.0, f"Expected 0.5-10.0s fallback, got {wait}"


# ── AC-6: _stop does not stop early on non-RateLimit TransientError ─


def test_ac6_stop_logic_simplified() -> None:
    """AC-6: _stop returns False at attempt 3 for generic TransientError."""

    from ado_odata_async.retry import _make_stop

    stop_fn = _make_stop(max_attempts=5)

    # Build state at attempt 3 with a TransientError
    state = _state_with_exception(TransientError("Service error"))
    state.attempt_number = 3

    # Should NOT stop (continue retrying) — still 2 attempts left
    assert stop_fn(state) is False
