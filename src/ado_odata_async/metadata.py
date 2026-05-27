"""$metadata fetch + cache. Used by entity validation (deferred)."""
from __future__ import annotations

from typing import Any


async def fetch_metadata(client: Any) -> dict[str, Any]:
    """Fetch OData $metadata and cache parsed CSDL.

    **Status**: Intentionally deferred (not in scope for Specs 001-012).
    **Rationale**: Entity validation via CSDL parsing requires:
    - CSDL XML parser (ElementTree) and schema traversal logic
    - Client-side type coercion (string->int, ISO8601->datetime, etc.)
    - Heavy test matrix (each entity x CSDL version combinations)
    - Currently, Pydantic `model_validate()` (strict mode) + type hints suffice.

    **Future Path**: Implement via separate Spec-013 if:
    - OData server metadata parsing is needed for discovery
    - Client-side validation layer deemed necessary
    - Schema migration tooling required

    **See Also**: Issue #XXXX (when created), PEP 563 (deferred annotations).
    """
    raise NotImplementedError("$metadata fetch is intentionally deferred")
