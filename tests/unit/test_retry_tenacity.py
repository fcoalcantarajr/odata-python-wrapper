"""Tests for SPEC-003 retry-tenacity — with_retry decorator.

GREEN (was RED phase; with_retry implemented).

  - AC-1: TransientError retries with backoff+jitter, succeeds on retry
  - AC-2: RateLimitError capped at 3 attempts regardless of max_attempts
  - AC-3: AuthenticationError NEVER retried (HR-15)
  - AC-4: BadRequestError NEVER retried
  - AC-5: Max retries exceeded propagates last TransientError (no wrapper)
  - AC-6: Configurable max_attempts / min_delay / max_delay respected
  - AC-7: @with_retry preserves async function signature and type hints
"""

from __future__ import annotations

import time

import pytest

from ado_odata_async.exceptions import (
    AuthenticationError,
    BadRequestError,
    RateLimitError,
    TransientError,
)
from ado_odata_async.retry import with_retry


@pytest.mark.asyncio
async def test_ac1_transient_retry_success_after_retries() -> None:
    """AC-1: TransientError triggers retry — succeeds on 3rd attempt."""
    call_count = 0

    async def fn() -> str:
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise TransientError("Service Unavailable")
        return "ok"

    wrapped = with_retry(fn)
    result = await wrapped()

    assert result == "ok"
    assert call_count == 3


@pytest.mark.asyncio
async def test_ac2_ratelimit_uses_same_max_attempts() -> None:
    """AC-2: RateLimitError uses the same max_attempts as other exceptions (SR-003).

    SR-003 simplified _make_stop — no early-stop for RateLimitError.
    With max_attempts=5, fn is called exactly 5 times.
    """
    call_count = 0

    async def fn() -> str:
        nonlocal call_count
        call_count += 1
        raise RateLimitError("Rate limited")

    wrapped = with_retry(fn, max_attempts=5)

    with pytest.raises(RateLimitError):
        await wrapped()

    assert call_count == 5


@pytest.mark.asyncio
async def test_ac3_auth_error_never_retried() -> None:
    """AC-3: AuthenticationError NEVER retried (HR-15)."""
    call_count = 0

    async def fn() -> str:
        nonlocal call_count
        call_count += 1
        raise AuthenticationError("Unauthorized")

    wrapped = with_retry(fn)

    with pytest.raises(AuthenticationError):
        await wrapped()

    assert call_count == 1


@pytest.mark.asyncio
async def test_ac4_bad_request_never_retried() -> None:
    """AC-4: BadRequestError NEVER retried."""
    call_count = 0

    async def fn() -> str:
        nonlocal call_count
        call_count += 1
        raise BadRequestError("Bad request")

    wrapped = with_retry(fn)

    with pytest.raises(BadRequestError):
        await wrapped()

    assert call_count == 1


@pytest.mark.asyncio
async def test_ac5_max_attempts_propagates_last_exception() -> None:
    """AC-5: Max retries exceeded propagates the last TransientError (no wrapper)."""
    call_count = 0

    async def fn() -> str:
        nonlocal call_count
        call_count += 1
        raise TransientError(f"Attempt #{call_count} failed")

    wrapped = with_retry(fn, max_attempts=3)

    with pytest.raises(TransientError) as exc_info:
        await wrapped()

    assert call_count == 3
    assert "Attempt #3" in str(exc_info.value)


@pytest.mark.asyncio
async def test_ac6_configurable_params_respected() -> None:
    """AC-6: Configurable max_attempts / min_delay / max_delay are respected."""
    call_count = 0

    async def fn() -> str:
        nonlocal call_count
        call_count += 1
        if call_count <= 4:
            raise TransientError("Service Unavailable")
        return "ok"

    t0 = time.monotonic()
    wrapped = with_retry(fn, max_attempts=5, min_delay=0.01, max_delay=0.05)
    result = await wrapped()
    elapsed = time.monotonic() - t0

    assert result == "ok"
    assert call_count == 5
    assert elapsed < 1.0


@pytest.mark.asyncio
async def test_ac7_decorator_preserves_signature() -> None:
    """AC-7: @with_retry preserves async signature and type hints."""

    @with_retry
    async def fetch_data(arg: int) -> str:
        return f"got {arg}"

    from typing import get_type_hints

    hints = get_type_hints(fetch_data)
    assert hints.get("arg") is int
    assert hints.get("return") is str
