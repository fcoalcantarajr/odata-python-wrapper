"""Pagination iterators. Async generator over $skip pages."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ado_odata_async.client import AdoODataClient

logger = logging.getLogger(__name__)


async def iter_pages(
    client: AdoODataClient,
    entity_set: str,
    *,
    top: int = 100,
    query: dict[str, str] | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Yield each page dict via $skip/$top or @odata.nextLink.

    Args:
        client: The AdoODataClient instance.
        entity_set: OData entity set name (e.g. "WorkItems").
        top: Page size ($top). Must be >= 1 (caller validates).
        query: Optional additional query parameters in canonical OData order.

    Yields:
        Each page response dict containing at least ``"value"``.
    """
    logger.debug("paginate.start: entity_set=%s top=%d query=%s", entity_set, top, query)
    skip = 0
    next_link_url: str | None = None

    while True:
        if next_link_url:
            data = await client._get_raw(next_link_url)
        else:
            # Build query params in canonical OData order (HR-9):
            #   $apply → $filter → $orderby → $expand → $select → $skip → $top
            merged: dict[str, str] = {}
            if query:
                merged.update(query)
            if skip > 0:
                merged["$skip"] = str(skip)
            merged["$top"] = str(top)
            data = await client.get(entity_set, **merged)

        items: list[Any] = data.get("value", [])
        next_link: Any = data.get("@odata.nextLink")

        if not items:
            break

        logger.debug(
            "paginate.page: entity_set=%s items=%d has_nextLink=%s",
            entity_set,
            len(items),
            bool(data.get("@odata.nextLink")),
        )
        yield data

        if next_link:
            next_link_url = str(next_link)
            continue

        if len(items) < top:
            break

        skip += len(items)
        next_link_url = None
