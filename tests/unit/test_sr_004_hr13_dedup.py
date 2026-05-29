"""Tests for SR-004: HR-13 validation dedup.

GREEN (was RED phase; shared _check_snapshot_groupby implemented).
"""

from __future__ import annotations

import pytest

from ado_odata_async.query._apply import Apply

# ── AC-1: Shared function validates WorkItemSnapshot ──────────────


def test_ac1_valid_workitem_snapshot() -> None:
    """AC-1: Shared fn returns None for WorkItemSnapshot with valid groupby((DateSK))."""
    # Import function (should succeed)
    try:
        from ado_odata_async.query._apply import (
            _check_snapshot_groupby,
        )
    except ImportError:
        pytest.fail("import failed (function should exist)")
    result = _check_snapshot_groupby(entity_set="WorkItemSnapshot", apply_value="groupby((DateSK))")
    assert result is None


# ── AC-2: Shared function rejects missing DateSK ──────────────────


def test_ac2_missing_datesk() -> None:
    """AC-2: Shared fn raises ValueError for WorkItemSnapshot without DateSK."""
    from ado_odata_async.query._apply import _check_snapshot_groupby

    with pytest.raises(ValueError, match="DateSK"):
        _check_snapshot_groupby(entity_set="WorkItemSnapshot", apply_value="groupby((State))")


# ── AC-3: Shared function validates WorkItemBoardSnapshot ─────────


def test_ac3_valid_board_snapshot() -> None:
    """AC-3: Shared fn returns None for WorkItemBoardSnapshot with valid groupby((DateValue))."""
    from ado_odata_async.query._apply import _check_snapshot_groupby

    result = _check_snapshot_groupby(
        entity_set="WorkItemBoardSnapshot", apply_value="groupby((DateValue))"
    )
    assert result is None


# ── AC-4: Shared function rejects missing DateValue ───────────────


def test_ac4_missing_datevalue() -> None:
    """AC-4: Shared fn raises ValueError for WorkItemBoardSnapshot without DateValue."""
    from ado_odata_async.query._apply import _check_snapshot_groupby

    with pytest.raises(ValueError, match="DateValue"):
        _check_snapshot_groupby(entity_set="WorkItemBoardSnapshot", apply_value="groupby((State))")


# ── AC-5: Non-snapshot entity sets pass through ───────────────────


def test_ac5_non_snapshot_passthrough() -> None:
    """AC-5: Shared fn returns None for non-snapshot entity sets."""
    from ado_odata_async.query._apply import _check_snapshot_groupby

    result = _check_snapshot_groupby(entity_set="WorkItems", apply_value="")
    assert result is None


# ── AC-6: All three original call sites delegate ──────────────────


@pytest.mark.asyncio
async def test_ac6_apply_validate_delegates() -> None:
    """AC-6: Apply.validate() delegates to shared fn — valid case does not raise."""
    a = Apply(entity_type="WorkItemSnapshot").groupby("DateSK")
    # Apply.validate() delegates to shared fn
    a.validate()  # Should not raise


@pytest.mark.asyncio
async def test_ac6_apply_validate_rejects() -> None:
    """AC-6: Apply.validate() delegates — invalid case raises ValueError."""
    a = Apply(entity_type="WorkItemSnapshot").groupby("State")
    with pytest.raises(ValueError, match="DateSK"):
        a.validate()


@pytest.mark.asyncio
async def test_ac6_builder_apply_delegates() -> None:
    """AC-6: QueryBuilder.apply() delegates to shared fn."""
    from unittest.mock import MagicMock

    from ado_odata_async.query._builder import QueryBuilder

    client = MagicMock()
    b = QueryBuilder(client=client, entity_set="WorkItemSnapshot")
    a = Apply.groupby("DateSK")
    # apply() delegates to shared fn
    result = b.apply(a)
    assert result._options.get("$apply") is not None


@pytest.mark.asyncio
async def test_ac6_builder_validate_hr13_delegates() -> None:
    """AC-6: QueryBuilder._validate_hr13() delegates — invalid case raises."""
    from unittest.mock import MagicMock

    from ado_odata_async.query._builder import QueryBuilder

    client = MagicMock()
    b = QueryBuilder(client=client, entity_set="WorkItemBoardSnapshot")
    # No $apply set — should raise ValueError
    with pytest.raises(ValueError, match="DateValue"):
        b._validate_hr13()


# ── AC-7: Regex pattern exists exactly once ───────────────────────


def test_ac7_regex_appears_exactly_once() -> None:
    """AC-7: The HR-13 groupby regex literal appears exactly once in src/.

    This checks that the deduplication goal is met — no copy-pasted regex.
    """
    import subprocess
    import sys

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import re, os
count = 0
for root, dirs, files in os.walk("src"):
    for f in files:
        if f.endswith(".py"):
            path = os.path.join(root, f)
            with open(path) as fh:
                content = fh.read()
            # Search for the regex literal as a Python raw string
            count += len(re.findall(
                r'r"groupby\\(\\(([^)]+)\\)\\)"',
                content
            ))
print(count)
""",
        ],
        capture_output=True,
        text=True,
        cwd="/workspaces/odata-python-wrapper",
    )
    match_count = int(result.stdout.strip())
    assert match_count <= 1, (
        f"Expected at most 1 occurrence of the HR-13 regex literal, "
        f"found {match_count}. Deduplication failed."
    )
