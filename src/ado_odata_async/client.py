"""Top-level async client. Single ClientSession (HR-7). v4.0-preview only (HR-19)."""

from __future__ import annotations

from types import TracebackType
from typing import Self

import aiohttp

# Single source of truth for the OData version (HR-19, HR-20).
# Rollback to "v2.0" requires ADR amendment + test fixture update.
ODATA_VERSION: str = "v4.0-preview"


class AdoODataClient:
    """Async client for Azure DevOps Analytics OData.

    Lifecycle: `async with AdoODataClient(...) as client:` ensures single
    ClientSession creation/close (HR-7) and propagates cancellation cleanly.
    """

    def __init__(self, *, org: str, project: str, pat: str) -> None:
        self._org = org
        self._project = project
        self._pat = pat
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> Self:
        raise NotImplementedError("SPEC-001 will implement session lifecycle")

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        raise NotImplementedError("SPEC-001 will implement session lifecycle")
