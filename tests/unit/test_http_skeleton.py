"""Tests for SPEC-001 HTTP skeleton — single session, v4.0-preview, empty-user BasicAuth.

All tests must FAIL (RED phase) against current stub code in src/.
"""

from __future__ import annotations

import pytest
from aioresponses import aioresponses

from ado_odata_async import AdoODataClient
from ado_odata_async.client import ODATA_VERSION


@pytest.mark.asyncio
async def test_ac1_session_reuse(
    fake_pat: str,
    fake_org: str,
    fake_project: str,
    mock_http: aioresponses,
) -> None:
    """AC-1: same ClientSession across calls."""
    async with AdoODataClient(
        org=fake_org,
        project=fake_project,
        pat=fake_pat,
    ) as c:
        s1 = c._session
        await c.get("WorkItems")
        await c.get("WorkItems")
        s2 = c._session
        assert s1 is s2


@pytest.mark.asyncio
async def test_ac2_session_closed_on_exit(
    fake_pat: str,
    fake_org: str,
    fake_project: str,
    mock_http: aioresponses,
) -> None:
    """AC-2: session closed on __aexit__."""
    async with AdoODataClient(
        org=fake_org,
        project=fake_project,
        pat=fake_pat,
    ) as c:
        pass
    assert c._session is None


@pytest.mark.asyncio
async def test_ac3_basicauth_empty_user(
    fake_pat: str,
    fake_org: str,
    fake_project: str,
    mock_http: aioresponses,
) -> None:
    """AC-3: BasicAuth with empty username."""
    async with AdoODataClient(
        org=fake_org,
        project=fake_project,
        pat=fake_pat,
    ) as c:
        auth = c._session.auth  # type: ignore[attr-defined]  # reason: aiohttp 3.13 exposes auth via auth property
        assert auth is not None
        assert auth.login == ""


@pytest.mark.asyncio
async def test_ac4_url_v4_preview(
    fake_pat: str,
    fake_org: str,
    fake_project: str,
    base_url: str,
    mock_http: aioresponses,
) -> None:
    """AC-4: URL targets v4.0-preview endpoint."""
    mock_http.get(
        f"{base_url}/WorkItems",
        payload={"value": []},
    )
    async with AdoODataClient(
        org=fake_org,
        project=fake_project,
        pat=fake_pat,
    ) as c:
        await c.get("WorkItems")


@pytest.mark.asyncio
async def test_ac5_odata_version_single_source(
    fake_pat: str,
) -> None:
    """AC-5: ODATA_VERSION is single source of truth."""
    assert ODATA_VERSION == "v4.0-preview"
    c = AdoODataClient(org="x", project="y", pat=fake_pat)
    r = repr(c)
    assert ODATA_VERSION in r


@pytest.mark.asyncio
async def test_ac6_double_enter_fails(
    fake_pat: str,
) -> None:
    """AC-6: double entry raises RuntimeError with 'already entered'."""
    c = AdoODataClient(org="x", project="y", pat=fake_pat)
    async with c:
        with pytest.raises(RuntimeError, match="already entered"):
            await c.__aenter__()


@pytest.mark.asyncio
async def test_ac7_pat_masked_in_repr(
    fake_org: str,
    fake_project: str,
) -> None:
    """AC-7: PAT masked in repr."""
    full_pat = "abcdef" * 10
    c = AdoODataClient(org=fake_org, project=fake_project, pat=full_pat)
    r = repr(c)
    assert full_pat not in r
    assert full_pat[:6] + "..." in r
