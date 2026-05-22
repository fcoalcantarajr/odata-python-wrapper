"""Tests for SPEC-009 WorkItem entity — frozen+strict Pydantic model.

All tests MUST FAIL (RED phase) because ``WorkItem`` model and
``client.get_workitem`` method don't exist yet in ``src/``.
"""

from __future__ import annotations

import re

import pytest
from aioresponses import aioresponses

from ado_odata_async import AdoODataClient


def test_ac1_required_fields() -> None:
    """AC-1: WorkItem has required fields: WorkItemId (int), Title (str), WorkItemType (Literal)."""
    from ado_odata_async import WorkItem

    row = {"WorkItemId": 42, "Title": "Fix login bug", "WorkItemType": "Bug"}
    instance = WorkItem.model_validate(row)
    assert instance.WorkItemId == 42
    assert isinstance(instance.Title, str)
    assert instance.WorkItemType == "Bug"


def test_ac2_extra_field_rejected() -> None:
    """AC-2: unknown field raises ValidationError with "Extra inputs are not permitted"."""
    from pydantic import ValidationError

    from ado_odata_async import WorkItem

    row = {
        "WorkItemId": 1,
        "Title": "x",
        "WorkItemType": "Bug",
        "FutureField": "surprise",
    }
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        WorkItem.model_validate(row)


def test_ac3_strict_type_enforcement() -> None:
    """AC-3: strict type rejects string literal where int is expected."""
    from pydantic import ValidationError

    from ado_odata_async import WorkItem

    row = {"WorkItemId": "abc", "Title": "x", "WorkItemType": "Bug"}
    with pytest.raises(ValidationError):
        WorkItem.model_validate(row)


@pytest.mark.asyncio
async def test_ac4_fetch_by_id(
    fake_pat: str,
    fake_org: str,
    fake_project: str,
    mock_http: aioresponses,
) -> None:
    """AC-4: client.get_workitem(42) returns WorkItem with WorkItemId=42."""
    from ado_odata_async import WorkItem

    mock_http.get(
        re.compile(r".*WorkItems.*"),
        payload={
            "value": [
                {"WorkItemId": 42, "Title": "Bug", "WorkItemType": "Bug"},
            ]
        },
    )
    async with AdoODataClient(
        org=fake_org,
        project=fake_project,
        pat=fake_pat,
    ) as c:
        result = await c.get_workitem(42)
    assert isinstance(result, WorkItem)
    assert result.WorkItemId == 42


def test_ac5_frozen_prevents_mutation() -> None:
    """AC-5: frozen model raises TypeError on attribute assignment."""
    from ado_odata_async import WorkItem

    instance = WorkItem(WorkItemId=1, Title="x", WorkItemType="Bug")
    with pytest.raises(TypeError, match="immutable"):
        instance.Title = "new"
