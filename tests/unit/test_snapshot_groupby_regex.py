"""Tests for AS-101: Fix snapshot groupby regex to match nested aggregate expressions.

GREEN (was RED phase; regex fixed in _apply.py:282).

The previous bug: regex ``groupby((([^)]+)))`` -- [^)]+ could not match ) chars,
so the trailing )) was unreachable for nested parens like
groupby((DateSK),aggregate(...)). The fix removed the trailing backslash-paren.
"""

from __future__ import annotations

import re

import pytest

from ado_odata_async.query._apply import _check_snapshot_groupby

# ── The buggy regex (as-is in _apply.py:282) ──────────────────────
BUGGY_REGEX = re.compile(r"groupby\(\(([^)]+)\)\)")
# ── The fix: remove trailing \) ────────────────────────────────────
FIXED_REGEX = re.compile(r"groupby\(\(([^)]+)\)")
# ── Entity set constants ───────────────────────────────────────────
SNAPSHOT = "WorkItemSnapshot"
BOARD_SNAPSHOT = "WorkItemBoardSnapshot"
NON_SNAPSHOT = "WorkItems"


# ===================================================================
# AC-1: Nested groupby + aggregate passes for WorkItemSnapshot
# ===================================================================
def test_ac1_nested_groupby_aggregate_passes() -> None:
    """AC-1: groupby((DateSK),aggregate(Count...)) should not raise."""
    # The fix (removed trailing \)) allows nested aggregate to match correctly.
    _check_snapshot_groupby(
        SNAPSHOT,
        "groupby((DateSK),aggregate(Count with sum as Total))",
    )


# ===================================================================
# AC-2: Simple groupby still works
# ===================================================================
def test_ac2_simple_groupby_still_passes() -> None:
    """AC-2: Simple groupby((DateSK)) must still work (backward compat)."""
    _check_snapshot_groupby(SNAPSHOT, "groupby((DateSK))")


# ===================================================================
# AC-3: Missing DateSK in nested form raises ValueError
# ===================================================================
def test_ac3_missing_required_nested_raises() -> None:
    """AC-3: Missing DateSK in nested form raises ValueError."""
    with pytest.raises(ValueError, match="requires groupby.DateSK."):
        _check_snapshot_groupby(
            SNAPSHOT,
            "groupby((State),aggregate(Count with sum as Total))",
        )


# ===================================================================
# AC-4: Missing DateSK in simple form raises ValueError
# ===================================================================
def test_ac4_missing_required_simple_raises() -> None:
    """AC-4: Missing DateSK in simple form raises ValueError."""
    with pytest.raises(ValueError, match="requires groupby.DateSK."):
        _check_snapshot_groupby(SNAPSHOT, "groupby((State))")


# ===================================================================
# AC-5: Non-snapshot entity is silently skipped
# ===================================================================
def test_ac5_non_snapshot_entity_skipped() -> None:
    """AC-5: Non-snapshot entity with any $apply returns None."""
    result = _check_snapshot_groupby(NON_SNAPSHOT, "groupby((DateSK))")
    assert result is None


# ===================================================================
# AC-6: Board snapshot with DateValue + aggregate passes
# ===================================================================
def test_ac6_board_snapshot_datevalue_aggregate_passes() -> None:
    """AC-6: Board snapshot with DateValue + aggregate should not raise."""
    _check_snapshot_groupby(
        BOARD_SNAPSHOT,
        "groupby((DateValue),aggregate(Effort with sum as Effort))",
    )


# ===================================================================
# AC-7: Regex captures only outer groupby fields
# ===================================================================
def test_ac7_regex_extracts_outer_fields_only() -> None:
    """AC-7: Regex must capture only the outer groupby fields."""
    m = FIXED_REGEX.search("groupby((DateSK,State),aggregate(...))")
    assert m is not None, f"Regex {FIXED_REGEX.pattern} did not match"
    assert m.group(1) == "DateSK,State"

    # Verify the BUGGY regex fails on this input
    m_buggy = BUGGY_REGEX.search("groupby((DateSK,State),aggregate(...))")
    assert m_buggy is None, (
        f"Buggy regex should NOT match nested aggregate but got: "
        f"{m_buggy.group(1) if m_buggy else 'None'}"
    )


# ===================================================================
# AC-8: Deeply nested aggregate functions pass
# ===================================================================
def test_ac8_deeply_nested_aggregates_pass() -> None:
    """AC-8: Deeply nested aggregate(SomeFunction(p1,p2)...) should pass."""
    _check_snapshot_groupby(
        SNAPSHOT,
        "groupby((DateSK),aggregate(SomeFunction(p1,p2) with sum as Total))",
    )
