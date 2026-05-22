"""Top-level async client. Single ClientSession (HR-7). v4.0-preview only (HR-19)."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from types import TracebackType
from typing import Any, Self, cast

import aiohttp
from yarl import URL

from ado_odata_async._http import build_url
from ado_odata_async.auth import mask_pat
from ado_odata_async.pagination import iter_pages

logger = logging.getLogger(__name__)

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
        self._entered: bool = False

    async def __aenter__(self) -> Self:
        if self._entered:
            raise RuntimeError("already entered")
        self._entered = True
        auth = aiohttp.BasicAuth("", self._pat)
        self._session = aiohttp.ClientSession(auth=auth)
        logger.debug("client entered — pat=%s odata=%s", mask_pat(self._pat), ODATA_VERSION)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        assert self._session is not None
        await self._session.close()
        self._session = None
        self._entered = False
        logger.debug("client exited — pat=%s odata=%s", mask_pat(self._pat), ODATA_VERSION)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}"
            f"(org={self._org!r}, project={self._project!r}, "
            f"pat={mask_pat(self._pat)!r}, odata={ODATA_VERSION!r})"
        )

    async def get(self, entity_set: str, **params: str) -> dict[str, Any]:
        assert self._session is not None
        base = URL(
            f"https://analytics.dev.azure.com/"
            f"{self._org}/{self._project}/_odata/{ODATA_VERSION}"
        )
        url = build_url(base, entity_set, query=params or None)
        async with self._session.get(url) as resp:
            resp.raise_for_status()
            return cast(dict[str, Any], await resp.json())

    def paginate(
        self,
        entity_set: str,
        *,
        top: int = 100,
        query: dict[str, str] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Paginate over entity_set, yielding each page dict.

        Args:
            entity_set: OData entity set name (e.g. ``"WorkItems"``).
            top: Page size (``$top``). Must be >= 1.
            query: Optional additional query parameters.

        Returns:
            AsyncIterator yielding page response dicts.

        Raises:
            ValueError: If *top* < 1.
        """
        if top < 1:
            raise ValueError("top must be >= 1")
        return iter_pages(self, entity_set, top=top, query=query)
