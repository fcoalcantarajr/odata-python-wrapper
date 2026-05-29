"""Tests for AS-102: Relax WorkItemType to accept custom work item types.

GREEN (was RED phase; constraint relaxed to str).
"""

from __future__ import annotations

import re as _re

import pytest
from pydantic import ValidationError

from ado_odata_async import WorkItem


# ── AC-1: Standard WorkItemType parses without error ───────────────
def test_ac1_standard_type_parses() -> None:
    """AC-1: Standard WorkItemType="Bug" parses without error."""
    row = {"WorkItemId": 1, "Title": "x", "WorkItemType": "Bug"}
    instance = WorkItem.model_validate(row)
    assert instance.WorkItemType == "Bug"


# ── AC-2: Custom WorkItemType parses without ValidationError ───────
def test_ac2_custom_type_no_validation_error() -> None:
    """AC-2: Custom WorkItemType="Initiative" must NOT raise ValidationError."""
    row = {"WorkItemId": 1, "Title": "x", "WorkItemType": "Initiative"}
    try:
        instance = WorkItem.model_validate(row)
    except ValidationError:
        pytest.fail("Custom WorkItemType raised ValidationError (AS-102 regression)")
    else:
        assert instance.WorkItemType == "Initiative"


# ── AC-3: Custom WorkItemType emits a logger warning ──────────────
def test_ac3_custom_type_logs_warning(caplog: pytest.LogCaptureFixture) -> None:
    """AC-3: Custom WorkItemType="OKR" logs a WARNING."""
    import logging

    caplog.set_level(logging.WARNING)
    row = {"WorkItemId": 1, "Title": "x", "WorkItemType": "OKR"}
    WorkItem.model_validate(row)
    assert any(
        _re.search(r"WorkItemType.*OKR.*not in standard set", msg) for msg in caplog.messages
    ), f"Expected warning about OKR not in standard set, got: {caplog.messages}"


# ── AC-4: Multiple custom types all succeed ────────────────────────
def test_ac4_multiple_custom_types() -> None:
    """AC-4: Multiple custom types all parse without ValidationError."""
    custom_types = ["Initiative", "OKR", "Spike", "Risk"]
    for wtype in custom_types:
        row = {"WorkItemId": 1, "Title": "x", "WorkItemType": wtype}
        instance = WorkItem.model_validate(row)
        assert instance.WorkItemType == wtype, f"Expected {wtype}, got {instance.WorkItemType}"


# ── AC-5: Standard type emits no logger warning ────────────────────
def test_ac5_standard_type_no_warning(caplog: pytest.LogCaptureFixture) -> None:
    """AC-5: Standard WorkItemType="Bug" emits no WARNING."""
    import logging

    caplog.set_level(logging.WARNING)
    row = {"WorkItemId": 1, "Title": "x", "WorkItemType": "Bug"}
    WorkItem.model_validate(row)
    for msg in caplog.messages:
        assert "not in standard set" not in msg, f"Unexpected warning: {msg}"


# ── AC-6: Frozen+strict model contract is preserved for custom types ─
def test_ac6_frozen_strict_preserved() -> None:
    """AC-6: Frozen+strict contract preserved for custom types."""
    instance = WorkItem(WorkItemId=1, Title="x", WorkItemType="Initiative")
    # Frozen check
    with pytest.raises(TypeError, match="immutable|frozen"):
        instance.WorkItemType = "Spike"
    # Extra field check
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        WorkItem.model_validate(
            {"WorkItemId": 1, "Title": "x", "WorkItemType": "Initiative", "Extra": "bad"}
        )


# ── AC-7: Custom type string is preserved verbatim ─────────────────
def test_ac7_custom_type_preserved_verbatim() -> None:
    """AC-7: Custom type string preserved exactly as-is."""
    verbatim = "MyOrg__Initiative_v2"
    row = {"WorkItemId": 1, "Title": "x", "WorkItemType": verbatim}
    instance = WorkItem.model_validate(row)
    assert instance.WorkItemType == verbatim
    assert isinstance(instance.WorkItemType, str)
