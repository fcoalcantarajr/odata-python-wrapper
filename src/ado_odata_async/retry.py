"""Retry decorator centralizing tenacity config."""

from __future__ import annotations

import logging
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

from tenacity import (
    RetryCallState,
    before_sleep_log,
    retry_if_exception_type,
)
from tenacity import retry as tenacity_retry

from ado_odata_async.exceptions import RateLimitError, TransientError

logger = logging.getLogger(__name__)

T = TypeVar("T")


def _make_wait(
    min_delay: float = 0.5, max_delay: float = 10.0
) -> Callable[[RetryCallState], float]:
    """Return a wait function that uses ``Retry-After`` when known, else jitter.

    If the last exception is a ``RateLimitError`` with a non-None
    ``retry_after``, returns that value.  Otherwise falls back to
    exponential jitter bounded by *min_delay* / *max_delay*.
    """

    def _wait(state: RetryCallState) -> float:
        outcome = state.outcome
        if outcome is not None:
            exc = outcome.exception()
            if isinstance(exc, RateLimitError) and exc.retry_after is not None:
                return exc.retry_after

        attempt = state.attempt_number or 1
        base = min_delay * (2 ** (attempt - 1))
        jitter = base * random.random() * 0.5  # noqa: S311  # jitter, not crypto
        return min(base + jitter, max_delay)  # type: ignore[no-any-return]  # reason: min(float, float) — mypy can't see it

    return _wait


def _make_stop(max_attempts: int = 5) -> Callable[[RetryCallState], bool]:
    """Return a stop function for the given *max_attempts*.

    Stops when *attempt_number* >= *max_attempts*.  All exception types
    (including ``RateLimitError``) use the same limit — no early-stop
    branch (SR-003 AC-6).
    """

    def _stop(state: RetryCallState) -> bool:
        return state.attempt_number >= max_attempts

    return _stop


def with_retry(
    fn: Callable[..., Awaitable[T]],
    max_attempts: int = 3,
    min_delay: float = 0.5,
    max_delay: float = 10.0,
) -> Callable[..., Awaitable[T]]:
    """Wrap an async fn with retry on TransientError only (HR-15).

    Retries on TransientError (and subclass RateLimitError).
    AuthenticationError and BadRequestError NEVER retry — they are not
    subclasses of TransientError, so the retry predicate rejects them.

    Args:
        fn: The async function to wrap.
        max_attempts: Maximum total attempts before giving up.
        min_delay: Minimum wait between retries (exponential jitter).
        max_delay: Maximum wait between retries.
    """
    retry_decorator = tenacity_retry(
        stop=_make_stop(max_attempts),
        wait=_make_wait(min_delay, max_delay),
        retry=retry_if_exception_type(TransientError),
        reraise=True,
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )

    return retry_decorator(fn)
