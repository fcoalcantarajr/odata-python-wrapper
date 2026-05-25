"""$metadata fetch + cache. Used by entity validation (deferred)."""
from __future__ import annotations

from typing import Any


async def fetch_metadata(client: Any) -> dict[str, Any]:
    """Fetch OData $metadata and cache parsed CSDL.

    Intentionally deferred — this stub exists as a placeholder for
    future implementation (out of scope for the initial 12 specs).
    """
    raise NotImplementedError("$metadata fetch is intentionally deferred")
