"""Tests for SPEC-013: Dependency graph per card — RED phase."""

from __future__ import annotations

import re

import pytest
from aioresponses import aioresponses

from ado_odata_async import AdoODataClient
from ado_odata_async.dependency_graph import fetch_dependency_links


@pytest.fixture
def fake_pat() -> str:
    return "PAT_" + "X" * 50


@pytest.fixture
def fake_org() -> str:
    return "myorg"


@pytest.fixture
def fake_project() -> str:
    return "myproject"


@pytest.fixture
def base_url(fake_org: str, fake_project: str) -> str:
    return f"https://analytics.dev.azure.com/{fake_org}" f"/{fake_project}/_odata/v4.0-preview"


# AC-1: Fetch dependency links for a batch of work items
@pytest.mark.asyncio
async def test_ac1_fetch_links_batch(fake_pat: str, base_url: str) -> None:
    """AC-1: Fetch Predecessor/Successor links for a batch of work items."""
    with aioresponses() as m:
        # Mock WorkItemLinks response using regex
        m.get(
            re.compile(r".*/WorkItemLinks.*"),
            payload={
                "value": [
                    {
                        "WorkItemLinkId": 1,
                        "SourceWorkItemId": 101,
                        "TargetWorkItemId": 102,
                        "LinkType": "Successor",
                        "LinkTypeReferenceName": "System.LinkTypes.Dependency-Forward",
                    },
                    {
                        "WorkItemLinkId": 2,
                        "SourceWorkItemId": 103,
                        "TargetWorkItemId": 101,
                        "LinkType": "Predecessor",
                        "LinkTypeReferenceName": "System.LinkTypes.Dependency-Reverse",
                    },
                ]
            },
        )

        async with AdoODataClient(org="myorg", project="myproject", pat=fake_pat) as client:
            result = await fetch_dependency_links(client, [101, 102, 103])

            # Verify structure
            assert 101 in result
            assert 102 in result
            assert 103 in result

            # Verify depends_on and blocks
            assert result[101]["depends_on"] == [103]
            assert result[101]["blocks"] == [102]
            assert result[102]["depends_on"] == [101]
            assert result[102]["blocks"] == []
            assert result[103]["depends_on"] == []
            assert result[103]["blocks"] == [101]


# AC-2: Handle work items with no dependencies
@pytest.mark.asyncio
async def test_ac2_no_dependencies(fake_pat: str, base_url: str) -> None:
    """AC-2: Handle work items with no dependencies."""
    with aioresponses() as m:
        m.get(re.compile(r".*/WorkItemLinks.*"), payload={"value": []})

        async with AdoODataClient(org="myorg", project="myproject", pat=fake_pat) as client:
            result = await fetch_dependency_links(client, [201, 202])

            assert 201 in result
            assert 202 in result
            assert result[201]["depends_on"] == []
            assert result[201]["blocks"] == []
            assert result[202]["depends_on"] == []
            assert result[202]["blocks"] == []


# AC-3: Page work items in batches of 200
@pytest.mark.asyncio
async def test_ac3_page_200(fake_pat: str, base_url: str) -> None:
    """AC-3: Page work items in batches of 200."""
    with aioresponses() as m:
        # Mock both GET and POST $batch (250 IDs trigger batch switch)
        m.get(re.compile(r".*/WorkItemLinks.*"), payload={"value": []}, repeat=True)
        # Mock batch response in proper multipart/mixed format
        batch_response = (
            b"--batchresponse_abc123\r\n"
            b"Content-Type: application/http\r\n"
            b"Content-Transfer-Encoding: binary\r\n"
            b"\r\n"
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: application/json\r\n"
            b"\r\n"
            b'{"value": []}\r\n'
            b"--batchresponse_abc123--\r\n"
        )
        m.post(
            re.compile(r".*/\$batch"),
            body=batch_response,
            repeat=True,
        )

        async with AdoODataClient(org="myorg", project="myproject", pat=fake_pat) as client:
            # 250 IDs should trigger 2 calls
            ids = list(range(1, 251))
            result = await fetch_dependency_links(client, ids)

            # Verify all IDs have entries
            assert len(result) == 250


# AC-4: Handle HTTP 429 with Retry-After
@pytest.mark.asyncio
async def test_ac4_retry_after_429(fake_pat: str, base_url: str) -> None:
    """AC-4: Handle HTTP 429 with Retry-After."""
    with aioresponses() as m:
        # First call returns 429
        m.get(re.compile(r".*/WorkItemLinks.*"), status=429, headers={"Retry-After": "1"})
        # Second call succeeds
        m.get(re.compile(r".*/WorkItemLinks.*"), payload={"value": []})

        async with AdoODataClient(org="myorg", project="myproject", pat=fake_pat) as client:
            result = await fetch_dependency_links(client, [101])
            # Should succeed after retry
            assert 101 in result


# AC-5: Resolve link-target titles within fetched set
@pytest.mark.asyncio
async def test_ac5_resolve_titles(fake_pat: str, base_url: str) -> None:
    """AC-5: Resolve link-target titles within fetched set."""
    with aioresponses() as m:
        m.get(
            re.compile(r".*/WorkItemLinks.*"),
            payload={
                "value": [
                    {
                        "WorkItemLinkId": 1,
                        "SourceWorkItemId": 101,
                        "TargetWorkItemId": 102,
                        "LinkType": "Successor",
                        "LinkTypeReferenceName": "System.LinkTypes.Dependency-Forward",
                    },
                ]
            },
        )
        # Mock WorkItems for title resolution
        m.get(
            re.compile(r".*/WorkItems.*"),
            payload={
                "value": [
                    {"WorkItemId": 101, "Title": "Card A"},
                    {"WorkItemId": 102, "Title": "Card B"},
                ]
            },
        )

        async with AdoODataClient(org="myorg", project="myproject", pat=fake_pat) as client:
            result = await fetch_dependency_links(client, [101, 102], resolve_titles=True)

            # Verify title resolution
            assert result[101]["blocks"] == [{"id": 102, "title": "Card B"}]


# AC-6: Flag overdue blocker as highest-risk
@pytest.mark.asyncio
async def test_ac6_flag_overdue(fake_pat: str, base_url: str) -> None:
    """AC-6: Flag overdue blocker as highest-risk."""
    with aioresponses() as m:
        m.get(
            re.compile(r".*/WorkItemLinks.*"),
            payload={
                "value": [
                    {
                        "WorkItemLinkId": 1,
                        "SourceWorkItemId": 101,
                        "TargetWorkItemId": 102,
                        "LinkType": "Successor",
                        "LinkTypeReferenceName": "System.LinkTypes.Dependency-Forward",
                    },
                ]
            },
        )
        # Mock WorkItems with overdue target
        m.get(
            re.compile(r".*/WorkItems.*"),
            payload={
                "value": [
                    {"WorkItemId": 101, "Title": "Card A"},
                    {
                        "WorkItemId": 102,
                        "Title": "Card B",
                        "ClosedDate": None,
                        "TargetDate": "2026-06-01",
                    },
                ]
            },
        )

        async with AdoODataClient(org="myorg", project="myproject", pat=fake_pat) as client:
            result = await fetch_dependency_links(client, [101, 102], flag_overdue=True)

            # Verify risk flag
            assert "overdue_blocker:102" in result[101]["risk_flags"]


# AC-7: Reusable component for hierarchy link type
@pytest.mark.asyncio
async def test_ac7_hierarchy_link_type(fake_pat: str, base_url: str) -> None:
    """AC-7: Reusable component for hierarchy link type."""
    with aioresponses() as m:
        m.get(
            re.compile(r".*/WorkItemLinks.*"),
            payload={
                "value": [
                    {
                        "WorkItemLinkId": 1,
                        "SourceWorkItemId": 101,
                        "TargetWorkItemId": 102,
                        "LinkType": "Child",
                        "LinkTypeReferenceName": "System.LinkTypes.Hierarchy-Forward",
                    },
                    {
                        "WorkItemLinkId": 2,
                        "SourceWorkItemId": 101,
                        "TargetWorkItemId": 103,
                        "LinkType": "Successor",
                        "LinkTypeReferenceName": "System.LinkTypes.Dependency-Forward",
                    },
                ]
            },
        )

        async with AdoODataClient(org="myorg", project="myproject", pat=fake_pat) as client:
            # Only hierarchy links
            result = await fetch_dependency_links(
                client,
                [101, 102, 103],
                link_type="System.LinkTypes.Hierarchy-Forward",
            )

            # Should only include hierarchy link, not dependency
            assert 102 in result[101]["blocks"]
            assert 103 not in result[101]["blocks"]
