"""Low-level HTTP helpers (request building, response parsing). Stubs."""

from __future__ import annotations

from typing import Any

import aiohttp
from yarl import URL


def build_url(base: URL, entity_set: str, query: dict[str, str] | None = None) -> URL:
    """Build a v4.0-preview entity-set URL with canonical query option ordering (HR-9)."""
    raise NotImplementedError("SPEC-007 will implement canonical query serializer")


async def parse_response(resp: aiohttp.ClientResponse) -> dict[str, Any]:
    """Parse JSON response, mapping HTTP 203+text/html to AuthenticationError (HR-15)."""
    raise NotImplementedError("SPEC-002 will implement response parsing")
