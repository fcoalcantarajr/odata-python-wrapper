"""Top-level async client. Single ClientSession (HR-7). v4.0-preview only (HR-19)."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from types import TracebackType
from typing import Any, Self

import aiohttp

from ado_odata_async._http import parse_response
from ado_odata_async.auth import build_basic_auth, mask_pat
from ado_odata_async.entities import WorkItem
from ado_odata_async.exceptions import TransientError
from ado_odata_async.pagination import iter_pages
from ado_odata_async.query._batch import (
    _BATCH_CONTENT_TYPE,
    build_batch_get_body,
    maybe_batch,
    parse_batch_response,
)
from ado_odata_async.query._builder import QueryBuilder
from ado_odata_async.query._serialize import serialize
from ado_odata_async.retry import with_retry

logger = logging.getLogger(__name__)

# Single source of truth for the OData version (HR-19, HR-20).
# Rollback to "v2.0" requires ADR amendment + test fixture update.
ODATA_VERSION: str = "v4.0-preview"


class AdoODataClient:
    """Async client for Azure DevOps Analytics OData.

    Lifecycle: `async with AdoODataClient(...) as client:` ensures single
    ClientSession creation/close (HR-7) and propagates cancellation cleanly.
    """

    def __init__(
        self,
        *,
        org: str,
        project: str,
        pat: str,
        batch_threshold: int = 3000,
        timeout: aiohttp.ClientTimeout | None = None,
    ) -> None:
        self._org = org
        self._project = project
        self._pat = pat
        self._batch_threshold = batch_threshold
        self._timeout: aiohttp.ClientTimeout = timeout or aiohttp.ClientTimeout(
            total=30.0, connect=10.0
        )
        self._session: aiohttp.ClientSession | None = None
        self._has_entered_once: bool = False

    async def __aenter__(self) -> Self:
        if self._has_entered_once:
            raise RuntimeError("re-entry forbidden — single ClientSession per client (HR-7)")
        self._has_entered_once = True
        self._session = aiohttp.ClientSession(
            auth=build_basic_auth(self._pat), timeout=self._timeout
        )
        logger.debug("client entered — pat=%s odata=%s", mask_pat(self._pat), ODATA_VERSION)
        return self

    @property
    def _service_root(self) -> str:
        return (
            f"https://analytics.dev.azure.com/"
            f"{self._org}/{self._project}/_odata/{ODATA_VERSION}"
        )

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        assert self._session is not None
        await self._session.close()
        self._session = None
        self._has_entered_once = True
        logger.debug("client exited — pat=%s odata=%s", mask_pat(self._pat), ODATA_VERSION)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}"
            f"(org={self._org!r}, project={self._project!r}, "
            f"pat={mask_pat(self._pat)!r}, odata={ODATA_VERSION!r})"
        )

    @with_retry
    async def get(self, entity_set: str, **params: str) -> dict[str, Any]:
        """Execute an OData GET request with optional query parameters.

        Constructs the full URL with serialized query options (respecting
        OData option order: $apply → $filter → $orderby → $expand →
        $select → $skip → $top per HR-9). Automatically switches to
        POST $batch multipart/mixed if the URL exceeds the batch threshold
        (default 3000 chars, HR-10).

        Args:
            entity_set: OData entity set name (e.g. "WorkItems",
                "WorkItemRevisions").
            **params: Query options as keyword arguments (e.g.
                $filter="State eq 'Active'", $top="100").

        Returns:
            Parsed JSON response dict from the OData service.

        Raises:
            RuntimeError: If called outside an async context manager
                (session not initialized).
            TransientError: On connection errors (wrapped from aiohttp).
            AuthenticationError: On HTTP 203 with text/html (HR-15,
                HR-8 gotcha 8) — not retried.
        """
        if self._session is None:
            raise RuntimeError(
                "client session is closed — .get() must be called within 'async with' context"
            )
        query_str = serialize(params) if params else ""
        url_str = f"{self._service_root}/{entity_set}"
        if query_str:
            url_str = f"{url_str}?{query_str}"

        return await self._execute_request(url_str)

    async def _execute_request(self, url_str: str) -> dict[str, Any]:
        """Execute an HTTP request, switching to POST $batch if URL is too long.

        Handles the batch/GET branching and response parsing. Called by ``get()``
        and directly for ``@odata.nextLink`` follow-through.
        """
        assert self._session is not None  # caller guarantees

        method, final_url = maybe_batch(
            "GET", url_str, service_root=self._service_root, threshold=self._batch_threshold
        )

        try:
            if method == "POST":
                logger.debug("batch switch: URL=%d chars -> POST $batch", len(url_str))
                body = build_batch_get_body(url_str, self._service_root)
                async with self._session.post(
                    final_url,
                    data=body.encode("utf-8"),
                    headers={"Content-Type": _BATCH_CONTENT_TYPE},
                ) as resp:
                    if resp.status != 200:
                        await parse_response(resp)
                    raw = await resp.read()
                    return dict(parse_batch_response(raw))
            else:
                async with self._session.get(final_url) as resp:
                    return await parse_response(resp)
        except aiohttp.ClientError as exc:
            raise TransientError(f"Connection error: {exc}") from exc

    @with_retry
    async def _get_raw(self, url: str) -> dict[str, Any]:
        """Fetch a raw URL directly (for @odata.nextLink follow-through).

        Bypasses URL construction and batch decision — the URL is used as-is.
        Retries on transient errors, matching ``get()`` behavior (HR-15).
        """
        assert self._session is not None  # caller guarantees
        try:
            async with self._session.get(url) as resp:
                return await parse_response(resp)
        except aiohttp.ClientError as exc:
            raise TransientError(f"Connection error: {exc}") from exc

    async def get_workitem(self, id_: int) -> WorkItem:
        """Fetch a single WorkItem by its WorkItemId.

        Makes one OData query with ``$filter=WorkItemId eq {id_}`` and
        ``$select=WorkItemId,Title,WorkItemType``. Returns the first result
        parsed into a frozen WorkItem model.

        Args:
            id_: The WorkItemId to fetch.

        Returns:
            WorkItem instance parsed from the OData response.

        Raises:
            IndexError: If no WorkItem with the given id_ is found.
            pydantic.ValidationError: If the response doesn't match the model.
        """
        data = await self.get(
            "WorkItems",
            **{
                "$filter": f"WorkItemId eq {id_}",
                "$select": "WorkItemId,Title,WorkItemType",
            },
        )
        return WorkItem.model_validate(data["value"][0])

    def paginate(
        self,
        entity_set: str,
        *,
        top: int = 100,
        query: dict[str, str] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Paginate over entity_set, yielding each page dict.

        Uses ``$skip/$top`` offset-based pagination with automatic
        ``@odata.nextLink`` following when present. Iteration terminates
        when a page has fewer items than ``top`` AND no nextLink.

        Args:
            entity_set: OData entity set name (e.g. ``"WorkItems"``).
            top: Page size (``$top``). Must be >= 1.
            query: Optional additional query parameters merged with
                ``$skip``/``$top``.

        Returns:
            AsyncIterator yielding page response dicts.

        Raises:
            ValueError: If *top* < 1.
        """
        if top < 1:
            raise ValueError("top must be >= 1")
        return iter_pages(self, entity_set, top=top, query=query)

    def query(self, entity_set: str) -> QueryBuilder:
        """Return a ``QueryBuilder`` bound to this client.

        Args:
            entity_set: OData entity set name (e.g. ``"WorkItems"``).

        Returns:
            ``QueryBuilder`` instance that can be chained with filter,
            select, top, etc. and then executed via ``.get()`` or
            ``.paginate()``.
        """
        return QueryBuilder(client=self, entity_set=entity_set)
