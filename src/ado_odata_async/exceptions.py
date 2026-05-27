"""Exception hierarchy. Retryability is encoded in the type, not in flags."""

from __future__ import annotations


class AdoODataError(Exception):
    """Base for all client errors."""


class AuthenticationError(AdoODataError):
    """401 or 203+text/html. NEVER retry (HR-15)."""


class BadRequestError(AdoODataError):
    """400 from ADO. Includes server-reported reason. NOT retryable."""


class TransientError(AdoODataError):
    """5xx / connection reset / timeout. Retryable by tenacity."""


class RateLimitError(TransientError):
    """429 with Retry-After hint. Retryable, but capped attempts."""

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        self.retry_after = retry_after
        super().__init__(message)
