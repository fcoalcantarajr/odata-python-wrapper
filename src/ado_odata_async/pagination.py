"""Pagination iterators. Async generator over $skip pages."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any


async def iter_pages(
    client: Any,
    entity_set: str,
    query: dict[str, str] | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Yield each page dict until $skip token exhausted."""
    raise NotImplementedError("SPEC-004 will implement pagination")
    yield {}  # type: ignore[unreachable]  # marca como async generator pro mypy
