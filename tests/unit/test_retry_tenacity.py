"""RED-phase tests for SPEC-003 retry-tenacity — with_retry decorator.

All 7 tests MUST fail (RED) because with_retry() in retry.py currently raises
NotImplementedError (or does not accept configuration kwargs yet).

After SPEC-003 implementation these tests will turn GREEN:
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
    """AC-1: TransientError triggers retry — succeeds on 3rd attempt.

    Current stub raises NotImplementedError → RED.
    After impl: fn fails with TransientError on calls 1 and 2,
    succeeds on call 3 → returns "ok", call_count == 3.
    """
    call_count = 0

    async def fn() -> str:
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise TransientError("Service Unavailable")
        return "ok"

    wrapped = with_retry(fn)
    # RED: with_retry raises NotImplementedError
    result = await wrapped()

    assert result == "ok"
    assert call_count == 3


@pytest.mark.asyncio
async def test_ac2_ratelimit_capped_at_three() -> None:
    """AC-2: RateLimitError capped at 3 attempts even if max_attempts=5.

    Current stub either raises NotImplementedError or TypeError
    (kwargs not yet accepted) → RED.
    After impl: RateLimitError always raised, fn called exactly 3 times.
    """
    call_count = 0

    async def fn() -> str:
        nonlocal call_count
        call_count += 1
        raise RateLimitError("Rate limited")

    wrapped = with_retry(fn, max_attempts=5)
    # RED: TypeError (kwargs not supported) or NotImplementedError

    with pytest.raises(RateLimitError):
        await wrapped()

    assert call_count == 3


@pytest.mark.asyncio
async def test_ac3_auth_error_never_retried() -> None:
    """AC-3: AuthenticationError NEVER retried (HR-15).

    Current stub raises NotImplementedError → RED.
    After impl: AuthenticationError propagates immediately,
    fn called exactly 1 time (zero retries).
    """
    call_count = 0

    async def fn() -> str:
        nonlocal call_count
        call_count += 1
        raise AuthenticationError("Unauthorized")

    wrapped = with_retry(fn)
    # RED: NotImplementedError

    with pytest.raises(AuthenticationError):
        await wrapped()

    assert call_count == 1


@pytest.mark.asyncio
async def test_ac4_bad_request_never_retried() -> None:
    """AC-4: BadRequestError NEVER retried.

    Current stub raises NotImplementedError → RED.
    After impl: BadRequestError propagates immediately,
    fn called exactly 1 time (zero retries).
    """
    call_count = 0

    async def fn() -> str:
        nonlocal call_count
        call_count += 1
        raise BadRequestError("Bad request")

    wrapped = with_retry(fn)
    # RED: NotImplementedError

    with pytest.raises(BadRequestError):
        await wrapped()

    assert call_count == 1


@pytest.mark.asyncio
async def test_ac5_max_attempts_propagates_last_exception() -> None:
    """AC-5: Max retries exceeded propagates the last TransientError (no wrapper).

    Current stub either raises NotImplementedError or TypeError
    (kwargs not yet accepted) → RED.
    After impl: fn always raises TransientError, max_attempts=3,
    the 3rd call's exception message is propagated as-is.
    """
    call_count = 0

    async def fn() -> str:
        nonlocal call_count
        call_count += 1
        raise TransientError(f"Attempt #{call_count} failed")

    wrapped = with_retry(fn, max_attempts=3)
    # RED: TypeError or NotImplementedError

    with pytest.raises(TransientError) as exc_info:
        await wrapped()

    assert call_count == 3
    assert "Attempt #3" in str(exc_info.value)


@pytest.mark.asyncio
async def test_ac6_configurable_params_respected() -> None:
    """AC-6: Configurable max_attempts / min_delay / max_delay are respected.

    Current stub either raises NotImplementedError or TypeError
    (kwargs not yet accepted) → RED.
    After impl: fn fails 4 times (TransientError), succeeds on 5th,
    call_count == 5, elapsed time < 1s due to small delays.
    """
    call_count = 0

    async def fn() -> str:
        nonlocal call_count
        call_count += 1
        if call_count <= 4:
            raise TransientError("Service Unavailable")
        return "ok"

    t0 = time.monotonic()
    wrapped = with_retry(fn, max_attempts=5, min_delay=0.01, max_delay=0.05)
    # RED: TypeError or NotImplementedError
    result = await wrapped()
    elapsed = time.monotonic() - t0

    assert result == "ok"
    assert call_count == 5
    assert elapsed < 1.0


@pytest.mark.asyncio
async def test_ac7_decorator_preserves_signature() -> None:
    """AC-7: @with_retry preserves async signature and type hints.

    Current stub raises NotImplementedError at decoration time → RED.
    After impl: @with_retry returns a wrapper with identical signature,
    inspect.signature shows `arg: int` param and `str` return annotation.
    """

    @with_retry
    async def fetch_data(arg: int) -> str:
        return f"got {arg}"

    # RED: NotImplementedError at decoration time (function never assigned)

    from typing import get_type_hints

    hints = get_type_hints(fetch_data)
    assert hints.get("arg") is int
    assert hints.get("return") is str
