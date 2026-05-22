"""RED-phase tests for SPEC-004 pagination — client.paginate() async iterator.

All 5 tests MUST fail (RED) because client.paginate() does not exist.
After SPEC-004 implementation these tests will turn GREEN.

Each test maps to one AC from specs/004-pagination.md:
  - AC-1: $skip advances across 3 pages, 25 total items
  - AC-2: @odata.nextLink is followed when present
  - AC-3: Page shorter than top stops iteration (no nextLink, len < top)
  - AC-4: top < 1 raises ValueError("top must be >= 1")
  - AC-5: Exhausted iterator raises StopAsyncIteration
"""

from __future__ import annotations

import pytest
from aioresponses import aioresponses

from ado_odata_async import AdoODataClient

pytestmark = pytest.mark.asyncio


async def test_ac1_skip_advances(
    fake_pat: str,
    fake_org: str,
    fake_project: str,
) -> None:
    """AC-1: $skip advances each iteration, 3 pages, 25 total items.

    Mock returns 10 items per page (first 2 pages), 5 on last = 25 total.
    Verifies: total items = 25, 3 pages, no 4th request.
    """
    base = (
        f"https://analytics.dev.azure.com/{fake_org}"
        f"/{fake_project}/_odata/v4.0-preview/WorkItems"
    )

    with aioresponses() as m:
        m.get(
            f"{base}?%24top=10",
            payload={"value": [{"Id": i} for i in range(10)]},
        )
        m.get(
            f"{base}?%24skip=10&%24top=10",
            payload={"value": [{"Id": i} for i in range(10, 20)]},
        )
        m.get(
            f"{base}?%24skip=20&%24top=10",
            payload={"value": [{"Id": i} for i in range(20, 25)]},
        )

        async with AdoODataClient(
            org=fake_org,
            project=fake_project,
            pat=fake_pat,
        ) as c:
            pages: list[dict] = []
            async for page in c.paginate("WorkItems", top=10):
                pages.append(page)

            total_items = sum(len(p["value"]) for p in pages)

            assert total_items == 25
            assert len(pages) == 3


async def test_ac2_nextlink_followed(
    fake_pat: str,
    fake_org: str,
    fake_project: str,
) -> None:
    """AC-2: @odata.nextLink is followed when present.

    First response includes @odata.nextLink with a $skiptoken URL.
    Second response has no nextLink → iteration stops.
    Verifies: exactly 2 pages yielded, 2nd request uses the nextLink URL.
    """
    base = (
        f"https://analytics.dev.azure.com/{fake_org}"
        f"/{fake_project}/_odata/v4.0-preview/WorkItems"
    )
    next_link = (
        f"https://analytics.dev.azure.com/{fake_org}"
        f"/{fake_project}/_odata/v4.0-preview/WorkItems?%24skiptoken=abc"
    )

    with aioresponses() as m:
        m.get(
            f"{base}?%24top=100",
            payload={
                "value": [{"Id": i} for i in range(10)],
                "@odata.nextLink": next_link,
            },
        )
        m.get(
            next_link,
            payload={"value": [{"Id": i} for i in range(10, 15)]},
        )

        async with AdoODataClient(
            org=fake_org,
            project=fake_project,
            pat=fake_pat,
        ) as c:
            pages: list[dict] = []
            async for page in c.paginate("WorkItems", top=100):
                pages.append(page)

            assert len(pages) == 2


async def test_ac3_empty_page_stops(
    fake_pat: str,
    fake_org: str,
    fake_project: str,
) -> None:
    """AC-3: Page shorter than top stops iteration.

    First page returns 10 items (no @odata.nextLink) with top=100.
    Since len(items) = 10 < 100 = top, paginator stops after 1 request.
    Verifies: only 1 HTTP request, 1 page yielded.
    """
    base = (
        f"https://analytics.dev.azure.com/{fake_org}"
        f"/{fake_project}/_odata/v4.0-preview/WorkItems"
    )

    with aioresponses() as m:
        m.get(
            f"{base}?%24top=100",
            payload={"value": [{"Id": i} for i in range(10)]},
        )

        async with AdoODataClient(
            org=fake_org,
            project=fake_project,
            pat=fake_pat,
        ) as c:
            pages: list[dict] = []
            async for page in c.paginate("WorkItems", top=100):
                pages.append(page)

            assert len(pages) == 1


async def test_ac4_invalid_top_raises_valueerror(
    fake_pat: str,
    fake_org: str,
    fake_project: str,
) -> None:
    """AC-4: top < 1 raises ValueError("top must be >= 1").

    Validation happens synchronously when paginate() is called,
    BEFORE entering the async for loop.
    """
    async with AdoODataClient(
        org=fake_org,
        project=fake_project,
        pat=fake_pat,
    ) as c:
        with pytest.raises(ValueError, match="top must be >= 1"):
            c.paginate("WorkItems", top=0)


async def test_ac5_async_iterator_protocol(
    fake_pat: str,
    fake_org: str,
    fake_project: str,
) -> None:
    """AC-5: Exhausted iterator raises StopAsyncIteration.

    Empty response yields zero pages; after the async for loop,
    calling __anext__() directly raises StopAsyncIteration.
    """
    base = (
        f"https://analytics.dev.azure.com/{fake_org}"
        f"/{fake_project}/_odata/v4.0-preview/WorkItems"
    )

    with aioresponses() as m:
        m.get(
            f"{base}?%24top=100",
            payload={"value": []},
        )

        async with AdoODataClient(
            org=fake_org,
            project=fake_project,
            pat=fake_pat,
        ) as c:
            paginator = c.paginate("WorkItems", top=100)

            async for _ in paginator:
                pass

            with pytest.raises(StopAsyncIteration):
                await paginator.__anext__()
