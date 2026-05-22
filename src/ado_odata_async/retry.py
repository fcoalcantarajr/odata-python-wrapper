"""Retry decorator centralizing tenacity config. Stubs."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


def with_retry(fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    """Wrap an async fn with retry on TransientError only (HR-15)."""
    raise NotImplementedError("SPEC-003 will implement tenacity wrapping")
