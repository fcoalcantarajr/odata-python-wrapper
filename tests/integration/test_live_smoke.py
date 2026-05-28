"""AS-005: Smoke integration test — live Azure DevOps access.

Requires environment variables:
  ADO_PAT, ADO_ORG, ADO_PROJECT

Run with: uv run pytest tests/integration/ --run-integration
"""

from __future__ import annotations

import os

import pytest

from ado_odata_async import AdoODataClient


def _env_or_skip(name: str) -> str:
    """Get env var or skip test if not set."""
    val = os.environ.get(name)
    if not val:
        pytest.skip(f"{name} not set — skipping integration test")
    return val


@pytest.mark.integration
@pytest.mark.asyncio
async def test_smoke_query_workitems_top1() -> None:
    """AC-1: Query WorkItems with $top=1 returns HTTP 200 and non-empty response.

    Given valid ADO_PAT, ADO_ORG, ADO_PROJECT environment variables
    When client.query("WorkItems").top(1).get() is called
    Then the response contains a "value" key with at least 1 item
    """
    pat = _env_or_skip("ADO_PAT")
    org = _env_or_skip("ADO_ORG")
    project = _env_or_skip("ADO_PROJECT")

    async with AdoODataClient(org=org, project=project, pat=pat) as client:
        result = await client.query("WorkItems").top(1).get()

    assert "value" in result
    assert len(result["value"]) >= 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_smoke_paginate_yields_pages() -> None:
    """AC-2: Paginate over WorkItems yields at least one page.

    Given valid ADO_PAT, ADO_ORG, ADO_PROJECT environment variables
    When client.paginate("WorkItems", top=1) is iterated
    Then at least one page is yielded with a "value" key
    """
    pat = _env_or_skip("ADO_PAT")
    org = _env_or_skip("ADO_ORG")
    project = _env_or_skip("ADO_PROJECT")

    pages = []
    async with AdoODataClient(org=org, project=project, pat=pat) as client:
        async for page in client.paginate("WorkItems", top=1):
            pages.append(page)
            if len(pages) >= 1:
                break

    assert len(pages) >= 1
    assert "value" in pages[0]
