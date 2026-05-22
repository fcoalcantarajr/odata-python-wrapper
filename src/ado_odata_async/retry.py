"""Retry decorator centralizing tenacity config."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from tenacity import (
    RetryCallState,
    before_sleep_log,
    retry_if_exception_type,
    wait_exponential_jitter,
)
from tenacity import retry as tenacity_retry

from ado_odata_async.exceptions import RateLimitError, TransientError

logger = logging.getLogger(__name__)

T = TypeVar("T")


def with_retry(
    fn: Callable[..., Awaitable[T]],
    max_attempts: int = 3,
    min_delay: float = 0.5,
    max_delay: float = 10.0,
) -> Callable[..., Awaitable[T]]:
    """Wrap an async fn with retry on TransientError only (HR-15).

    Retries on TransientError (and subclass RateLimitError).
    RateLimitError is capped at min(max_attempts, 3) attempts.
    AuthenticationError and BadRequestError NEVER retry — they are not
    subclasses of TransientError, so the retry predicate rejects them.

    Args:
        fn: The async function to wrap.
        max_attempts: Maximum total attempts before giving up.
        min_delay: Minimum wait between retries (exponential jitter).
        max_delay: Maximum wait between retries.
    """
    rate_limit_max = min(max_attempts, 3)

    def _stop(retry_state: RetryCallState) -> bool:
        if retry_state.attempt_number >= max_attempts:
            return True
        if retry_state.attempt_number >= rate_limit_max:
            outcome = retry_state.outcome
            if outcome is not None:
                exc = outcome.exception()
                if exc is not None and isinstance(exc, RateLimitError):
                    return True
        return False

    retry_decorator = tenacity_retry(
        stop=_stop,
        wait=wait_exponential_jitter(initial=min_delay, max=max_delay),
        retry=retry_if_exception_type(TransientError),
        reraise=True,
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )

    return retry_decorator(fn)
