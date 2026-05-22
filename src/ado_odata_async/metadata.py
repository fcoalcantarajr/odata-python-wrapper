"""$metadata fetch + cache. Used by entity validation. Stubs."""

from __future__ import annotations

from typing import Any


async def fetch_metadata(client: Any) -> dict[str, Any]:
    """Fetch OData $metadata and cache parsed CSDL. Version via ODATA_VERSION constant."""
    raise NotImplementedError("SPEC-012 will implement metadata fetch")
