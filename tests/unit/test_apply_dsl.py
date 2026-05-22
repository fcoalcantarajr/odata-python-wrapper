"""RED-phase tests for SPEC-006 $apply DSL builder — fluent builder for OData aggregations.

All 8 tests MUST fail (RED) because `ado_odata_async.query._apply.Apply`
does not exist yet. The import itself will raise `ImportError`.

No async, no aiohttp, no fixtures needed — these are pure sync string
assertions against `Apply.build()` / `str(Apply)`.

Each test maps to one AC from specs/006-apply-dsl.md:
  - AC-1: groupby single field          → "$apply=groupby((State))"
  - AC-2: groupby multiple fields        → "$apply=groupby((State,Priority))"
  - AC-3: filter wrapping                → "$apply=filter(State eq 'Active')"
  - AC-4: aggregate method               → "$apply=aggregate(Effort with sum)"
  - AC-5: groupby then aggregate         → "$apply=groupby((...))/aggregate(...)"
  - AC-6: multiple aggregations          → contains "aggregate(Count with sum, Effort with avg)"
  - AC-7: WorkItemSnapshot no groupby    → ValueError with "WorkItemSnapshot" and "groupby(DateSK)"
  - AC-8: WorkItemBoardSnapshot w/groupby  → validate() returns None
"""

from __future__ import annotations

import pytest

from ado_odata_async.query._apply import Apply
from ado_odata_async.query._filter import Filter


def test_ac1_groupby_single_field() -> None:
    """AC-1: groupby single field.

    Apply.groupby("State").build()
      → "$apply=groupby((State))"

    Asserts:
      - build() returns "$apply=groupby((State))"
    """
    result = Apply.groupby("State").build()
    assert result == "$apply=groupby((State))"


def test_ac2_groupby_multiple_fields() -> None:
    """AC-2: groupby multiple fields.

    Apply.groupby(["State","Priority"]).build()
      → "$apply=groupby((State,Priority))"

    Asserts:
      - build() returns "$apply=groupby((State,Priority))"
    """
    result = Apply.groupby(["State", "Priority"]).build()
    assert result == "$apply=groupby((State,Priority))"


def test_ac3_filter_wrapping() -> None:
    """AC-3: filter wraps a Filter expression from SPEC-005.

    Apply.filter(Filter.eq("State", "Active")).build()
      → "$apply=filter(State eq 'Active')"

    Asserts:
      - build() returns "$apply=filter(State eq 'Active')"
    """
    f = Filter.eq("State", "Active")
    result = Apply.filter(f).build()
    assert result == "$apply=filter(State eq 'Active')"


def test_ac4_aggregate_method() -> None:
    """AC-4: aggregate with field name and method function.

    Apply.aggregate("Effort", "sum").build()
      → "$apply=aggregate(Effort with sum)"

    Asserts:
      - build() returns "$apply=aggregate(Effort with sum)"
    """
    result = Apply.aggregate("Effort", "sum").build()
    assert result == "$apply=aggregate(Effort with sum)"


def test_ac5_groupby_then_aggregate() -> None:
    """AC-5: groupby composed with aggregate (fluent chain).

    Apply.groupby(["TeamProject","WorkItemType"]).aggregate("Count","sum").build()
      → "$apply=groupby((TeamProject,WorkItemType))/aggregate(Count with sum)"

    Asserts:
      - build() returns the full composed $apply string
    """
    result = Apply.groupby(["TeamProject", "WorkItemType"]).aggregate("Count", "sum").build()
    assert result == ("$apply=groupby((TeamProject,WorkItemType))/aggregate(Count with sum)")


def test_ac6_multiple_aggregations() -> None:
    """AC-6: multiple aggregations in the same groupby scope.

    Apply.groupby("State").aggregate("Count","sum").aggregate("Effort","avg").build()
      → result contains "aggregate(Count with sum, Effort with avg)"

    Asserts:
      - build() contains "aggregate(Count with sum, Effort with avg)"
    """
    result = Apply.groupby("State").aggregate("Count", "sum").aggregate("Effort", "avg").build()
    assert "aggregate(Count with sum, Effort with avg)" in result


def test_ac7_enforce_snapshot_requires_groupby() -> None:
    """AC-7: WorkItemSnapshot without groupby(DateSK) raises ValueError (HR-13).

    Apply(entity_type="WorkItemSnapshot").validate()
      → ValueError with "WorkItemSnapshot" and "groupby(DateSK)"

    Asserts:
      - validate() raises ValueError
      - error message contains "WorkItemSnapshot"
      - error message contains "groupby(DateSK)"
    """
    apply_obj = Apply(entity_type="WorkItemSnapshot")
    with pytest.raises(ValueError, match=r"WorkItemSnapshot.*groupby\(DateSK\)") as exc_info:
        apply_obj.validate()
    msg = str(exc_info.value)
    assert "WorkItemSnapshot" in msg
    assert "groupby(DateSK)" in msg


def test_ac8_enforce_snapshot_with_valid_groupby() -> None:
    """AC-8: WorkItemBoardSnapshot with groupby(DateValue) passes validation (HR-13).

    Apply(entity_type="WorkItemBoardSnapshot").groupby("DateValue").validate()
      → None

    Asserts:
      - validate() returns None (no exception raised)
    """
    result = Apply(entity_type="WorkItemBoardSnapshot").groupby("DateValue").validate()
    assert result is None
