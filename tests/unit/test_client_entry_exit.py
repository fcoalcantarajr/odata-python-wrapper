"""Tests for AS-003: client entry/exit lifecycle — remove redundant _entered guard."""

from __future__ import annotations

import pytest

from ado_odata_async import AdoODataClient


@pytest.mark.asyncio
async def test_ac1_single_entry_succeeds(fake_pat: str) -> None:
    """AC-1: Single entry into context manager succeeds.

    Given an AdoODataClient instance
    When __aenter__ is called once
    Then no RuntimeError is raised
    """
    c = AdoODataClient(org="x", project="y", pat=fake_pat)
    async with c:
        assert c._session is not None


@pytest.mark.asyncio
async def test_ac2_reentry_after_exit_raises_runtime_error(fake_pat: str) -> None:
    """AC-2: Re-entry after exit raises RuntimeError.

    Given an AdoODataClient that has been entered and exited
    When __aenter__ is called again
    Then RuntimeError is raised with message containing "re-entry forbidden"
    """
    c = AdoODataClient(org="x", project="y", pat=fake_pat)
    async with c:
        pass
    with pytest.raises(RuntimeError, match="re-entry forbidden"):
        async with c:
            pass


@pytest.mark.asyncio
async def test_ac3_has_entered_once_set_on_exit(fake_pat: str) -> None:
    """AC-3: _has_entered_once is True after exit.

    Given an AdoODataClient that has been entered and exited
    When inspecting _has_entered_once
    Then _has_entered_once is True
    """
    c = AdoODataClient(org="x", project="y", pat=fake_pat)
    async with c:
        pass
    assert c._has_entered_once is True


@pytest.mark.asyncio
async def test_ac4_no_entered_attribute(fake_pat: str) -> None:
    """AC-4: _entered attribute is removed (AS-003 fix).

    Given an AdoODataClient instance
    When inspecting the instance
    Then _entered attribute does not exist
    """
    c = AdoODataClient(org="x", project="y", pat=fake_pat)
    assert not hasattr(c, "_entered")
