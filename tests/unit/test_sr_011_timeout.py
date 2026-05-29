"""Tests for SR-011: Configurable ClientSession timeout.

GREEN (was RED phase; timeout kwarg implemented).
"""

from __future__ import annotations

import aiohttp
import pytest

from ado_odata_async import AdoODataClient

# ── AC-1: Default timeout is 30s total ─────────────────────────────


@pytest.mark.asyncio
async def test_ac1_default_timeout_is_30s_total(fake_pat: str) -> None:
    """AC-1: When no timeout arg is provided, default total is 30s."""
    async with AdoODataClient(org="o", project="p", pat=fake_pat) as client:
        assert client._timeout.total == 30.0


# ── AC-2: Connect timeout is 10s ───────────────────────────────────


@pytest.mark.asyncio
async def test_ac2_connect_timeout_is_10s(fake_pat: str) -> None:
    """AC-2: When no timeout arg is provided, default connect is 10s."""
    async with AdoODataClient(org="o", project="p", pat=fake_pat) as client:
        assert client._timeout.connect == 10.0


# ── AC-3: Custom timeout via constructor ────────────────────────────


@pytest.mark.asyncio
async def test_ac3_custom_timeout_via_constructor(fake_pat: str) -> None:
    """AC-3: Custom timeout passed via constructor is stored."""
    t = aiohttp.ClientTimeout(total=5.0, connect=2.0)
    client = AdoODataClient(org="o", project="p", pat=fake_pat, timeout=t)
    async with client:
        assert client._timeout is t


# ── AC-4: Timeout is stored and accessible ──────────────────────────


@pytest.mark.asyncio
async def test_ac4_timeout_stored_and_accessible(fake_pat: str) -> None:
    """AC-4: Custom timeout is stored and accessible after construction."""
    t = aiohttp.ClientTimeout(total=5.0, connect=2.0)
    client = AdoODataClient(org="o", project="p", pat=fake_pat, timeout=t)
    async with client:
        assert client._timeout is t
        assert client._timeout.total == 5.0
        assert client._timeout.connect == 2.0


# ── AC-4b: Backward compatible — batch_threshold still works ───────


@pytest.mark.asyncio
async def test_ac4b_backward_compatible_batch_threshold(
    fake_pat: str,
) -> None:
    """AC-4b: Existing batch_threshold kwarg works alongside timeout."""
    client = AdoODataClient(org="o", project="p", pat=fake_pat, batch_threshold=5000)
    async with client:
        assert client._batch_threshold == 5000
        assert client._timeout.total == 30.0


# ── AC-5: Single ClientSession reuse preserved (HR-7) ──────────────


@pytest.mark.asyncio
async def test_ac5_single_clientsession_reuse_preserved(
    fake_pat: str,
) -> None:
    """AC-5: Session id is stable across multiple requests (HR-7 guard)."""
    from aioresponses import aioresponses

    t = aiohttp.ClientTimeout(total=5.0)
    client = AdoODataClient(org="o", project="p", pat=fake_pat, timeout=t)
    async with client:
        session_id = id(client._session)
        with aioresponses() as m:
            url = "https://analytics.dev.azure.com/o/p/_odata/v4.0-preview/WorkItems"
            m.get(url, payload={"value": []}, repeat=True)
            await client.get("WorkItems")
            await client.get("WorkItems")
        assert id(client._session) == session_id, "HR-7 violated: session recreated"
