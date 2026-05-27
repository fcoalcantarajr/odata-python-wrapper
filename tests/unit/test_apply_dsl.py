"""RED-phase tests for SPEC-006 $apply DSL builder — fluent builder for OData aggregations.

All 8 tests MUST fail (RED) because `ado_odata_async.query._apply.Apply`
does not exist yet. The import itself will raise `ImportError`.

No async, no aiohttp, no fixtures needed — these are pure sync string
assertions against `Apply.build()` / `str(Apply)`.

Each test maps to one AC from specs/006-apply-dsl.md:
  - AC-1: groupby single field          → "$apply=groupby((State))"
  - AC-2: groupby multiple fields        → "$apply=groupby((State,Priority))"
  - AC-3: filter wrapping                → "$apply=filter(State eq 'Active')"
   - AC-4: aggregate method               → "$apply=aggregate(Effort with sum as Effort)"
  - AC-5: groupby then aggregate         → "$apply=groupby((...))/aggregate(...)"
   - AC-6: multiple aggregations          → contains "aggregate(Count with sum as Count,"
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
      → "$apply=aggregate(Effort with sum as Effort)"

    Asserts:
      - build() returns "$apply=aggregate(Effort with sum as Effort)"
    """
    result = Apply.aggregate("Effort", "sum").build()
    # spec-correction: SPEC-006 requires "as <alias>" per OData v4.0
    assert result == "$apply=aggregate(Effort with sum as Effort)"


def test_ac5_groupby_then_aggregate() -> None:
    """AC-5: groupby composed with aggregate (fluent chain).

    Apply.groupby(["TeamProject","WorkItemType"]).aggregate("Count","sum").build()
      → "$apply=groupby((TeamProject,WorkItemType),aggregate(Count with sum as Count))"

    Asserts:
      - build() returns the full composed $apply string with nested aggregate
    """
    result = Apply.groupby(["TeamProject", "WorkItemType"]).aggregate("Count", "sum").build()
    # F12: aggregate is nested inside groupby when consecutive
    assert result == "$apply=groupby((TeamProject,WorkItemType),aggregate(Count with sum as Count))"


def test_ac6_multiple_aggregations() -> None:
    """AC-6: multiple aggregations in the same groupby scope.

    Apply.groupby("State").aggregate("Count","sum").aggregate("Effort","average").build()
      → result contains "aggregate(Count with sum as Count, Effort with average as Effort)"

    Asserts:
      - build() contains "aggregate(Count with sum as Count, Effort with average as Effort)"
    """
    result = Apply.groupby("State").aggregate("Count", "sum").aggregate("Effort", "average").build()
    # spec-correction: SPEC-006 requires "as <alias>" per OData v4.0
    assert "aggregate(Count with sum as Count, Effort with average as Effort)" in result


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


def test_instance_level_groupby() -> None:
    """Instance-level groupby mutation (fluent chaining).

    apply_instance = Apply()
    apply_instance.groupby("State")
      → returns Apply instance with groupby set, can chain further

    Asserts:
      - instance.groupby() returns self (fluent)
      - build() reflects the groupby
    """
    apply_obj = Apply()
    result = apply_obj.groupby("State")
    assert result is apply_obj
    assert result.build() == "$apply=groupby((State))"


def test_str_method() -> None:
    """__str__ method returns same as build().

    Apply.groupby("State").__str__()
      → same as .build() result

    Asserts:
      - str(apply) == apply.build()
    """
    apply_obj = Apply.groupby("State")
    assert str(apply_obj) == apply_obj.build()
    assert str(apply_obj) == "$apply=groupby((State))"


def test_workitem_board_snapshot_without_datevalue() -> None:
    """WorkItemBoardSnapshot without groupby(DateValue) raises ValueError (HR-13).

    Apply(entity_type="WorkItemBoardSnapshot").validate()
      → ValueError with "WorkItemBoardSnapshot" and "groupby(DateValue)"

    Asserts:
      - validate() raises ValueError
      - error message contains "WorkItemBoardSnapshot"
      - error message contains "groupby(DateValue)"
    """
    apply_obj = Apply(entity_type="WorkItemBoardSnapshot")
    with pytest.raises(ValueError, match=r"WorkItemBoardSnapshot.*groupby\(DateValue\)"):
        apply_obj.validate()


def test_instance_aggregate_chaining() -> None:
    """Instance aggregate mutation can be chained.

    apply_instance = Apply()
    apply_instance.aggregate("Count", "sum").aggregate("Effort", "average")
      → returns Apply with both aggregations

    Asserts:
      - returns fluent Apply instance
      - build() reflects both aggregations
    """
    apply_obj = Apply()
    result = apply_obj.aggregate("Count", "sum")
    assert result is apply_obj
    result2 = result.aggregate("Effort", "average")
    assert result2 is apply_obj
    # spec-correction: SPEC-006 requires "as <alias>" per OData v4.0
    expected = "$apply=aggregate(Count with sum as Count, Effort with average as Effort)"
    assert expected in result2.build()


def test_instance_filter_chaining() -> None:
    """Instance filter mutation can be chained.

    apply_instance = Apply()
    apply_instance.filter(Filter.eq(...)).groupby("State")
      → returns Apply with both filter and groupby

    Asserts:
      - returns fluent Apply instance
      - build() reflects both filter and groupby
    """
    f = Filter.eq("State", "Active")
    apply_obj = Apply()
    result = apply_obj.filter(f)
    assert result is apply_obj
    result2 = result.groupby("State")
    assert result2 is apply_obj
    assert "$apply=filter(State eq 'Active')/groupby((State))" in result2.build()


def test_groupby_with_tuple() -> None:
    """Groupby with tuple (not just list) is converted to list."""
    result = Apply.groupby(("State", "Priority")).build()
    assert result == "$apply=groupby((State,Priority))"


def test_empty_apply() -> None:
    """Empty Apply with no clauses builds to just $apply= (edge case)."""
    result = Apply().build()
    assert result == "$apply="


def test_filter_then_groupby() -> None:
    """Filter then groupby preserves declaration order.

    Per OData spec, order should match method call order: groupby
    is called first, then filter.

    Asserts:
      - build() preserves declaration order (groupby, then filter)
    """
    f = Filter.eq("Priority", "High")
    result = Apply.groupby("State").filter(f).build()
    # HR-9: $apply → $filter → $orderby...
    # Within $apply: groupby() then filter()
    parts = result.split("/")
    assert parts[0].startswith("$apply=groupby")
    assert "filter" in result


# -----------------------------------------------------------------------
# F10: declaration-order preservation in $apply pipeline
# -----------------------------------------------------------------------


def test_f10_filter_groupby_aggregate_order() -> None:
    """F10 exact case: Apply().filter(...).groupby(...).aggregate(...)
    emits filter→groupby→aggregate in declaration order.

    This is the regression test for F10 — the pipeline MUST preserve the
    order in which the user chained the methods, not a hardcoded order.
    """
    result = (
        Apply()
        .filter(Filter.eq("StateCategory", "Completed"))
        .groupby("DateSK", "State")
        .aggregate("$count", alias="Count")
        .build()
    )
    assert result == (
        "$apply=filter(StateCategory eq 'Completed')"
        "/groupby((DateSK,State),aggregate($count as Count))"
    )


def test_f10_all_6_permutations() -> None:
    """All 6 permutations of filter/groupby/aggregate preserve order."""
    f1 = Filter.eq("A", "1")
    f2 = Filter.gt("B", "2")

    # Permutation 1: filter → groupby → aggregate
    r = Apply().filter(f1).groupby("X").aggregate("Y", "sum").build()
    assert r.index("filter") < r.index("groupby") < r.index("aggregate")

    # Permutation 2: filter → aggregate → groupby
    r = Apply().filter(f1).aggregate("Y", "sum").groupby("X").build()
    assert r.index("filter") < r.index("aggregate") < r.index("groupby")

    # Permutation 3: groupby → filter → aggregate
    r = Apply().groupby("X").filter(f1).aggregate("Y", "sum").build()
    assert r.index("groupby") < r.index("filter") < r.index("aggregate")

    # Permutation 4: groupby → aggregate → filter
    r = Apply().groupby("X").aggregate("Y", "sum").filter(f1).build()
    assert r.index("groupby") < r.index("aggregate") < r.index("filter")

    # Permutation 5: aggregate → filter → groupby
    r = Apply().aggregate("Y", "sum").filter(f1).groupby("X").build()
    assert r.index("aggregate") < r.index("filter") < r.index("groupby")

    # Permutation 6: aggregate → groupby → filter
    r = Apply().aggregate("Y", "sum").groupby("X").filter(f1).build()
    assert r.index("aggregate") < r.index("groupby") < r.index("filter")

    # Permutation 6b: all three with filter+filter
    r = Apply().filter(f1).groupby("X").filter(f2).aggregate("Y", "sum").build()
    assert r.index("filter(A") < r.index("groupby") < r.index("filter(B") < r.index("aggregate")


def test_f10_consecutive_aggregate_coalesce() -> None:
    """Consecutive .aggregate().aggregate() coalesce into one clause."""
    result = (
        Apply()
        .groupby("State")
        .aggregate("Count", "sum")
        .aggregate("Effort", "average")
        .build()
    )
    # Single aggregate clause with both metrics, nested inside groupby (F12)
    assert result == (
        "$apply=groupby((State),"
        "aggregate(Count with sum as Count, Effort with average as Effort))"
    )


def test_f10_non_consecutive_aggregate_two_clauses() -> None:
    """Non-consecutive aggregate does NOT coalesce — two separate clauses."""
    result = (
        Apply()
        .aggregate("Count", "sum")
        .groupby("State")
        .aggregate("Effort", "average")
        .build()
    )
    # Two separate aggregate clauses
    assert "aggregate(Count with sum as Count)" in result
    assert "aggregate(Effort with average as Effort)" in result
    # groupby between them
    cnt_idx = result.index("aggregate(Count")
    gb_idx = result.index("groupby")
    efr_idx = result.index("aggregate(Effort")
    assert cnt_idx < gb_idx < efr_idx


def test_f10_hr13_still_enforced() -> None:
    """HR-13 still raises on WorkItemSnapshot without DateSK after refactor."""
    apply_obj = Apply(entity_type="WorkItemSnapshot").aggregate("Count", "sum")
    with pytest.raises(ValueError, match=r"WorkItemSnapshot.*groupby\(DateSK\)"):
        apply_obj.validate()


def test_f10_multiple_filters_append() -> None:
    """Multiple .filter() calls append, not replace — each is a separate
    pipeline step. This is the intended F10 semantics: operations are
    added to the pipeline in declaration order."""
    f1 = Filter.eq("State", "Active")
    f2 = Filter.gt("Priority", "High")
    result = Apply().filter(f1).filter(f2).build()
    assert result == (
        "$apply=filter(State eq 'Active')/filter(Priority gt 'High')"
    )


def test_f10_groupby_repositioned_by_second_call() -> None:
    """Second .groupby() replaces the first at its original position
    (idempotency), preserving the relative ordering with other ops."""
    f = Filter.eq("State", "Active")
    result = (
        Apply()
        .groupby("Priority")
        .filter(f)
        .groupby("State")  # replaces groupby(Priority) at position 0
        .build()
    )
    # groupby is still before filter (since it was declared before filter)
    assert result == (
        "$apply=groupby((State))/filter(State eq 'Active')"
    )


def test_f10_empty_groupby_raises() -> None:
    """Empty groupby() raises ValueError (invalid OData)."""
    with pytest.raises(ValueError, match="requires at least one field"):
        Apply().groupby()  # type: ignore[call-arg]  # reason: intentional empty call to test guard
    with pytest.raises(ValueError, match="requires at least one field"):
        Apply().groupby([])


def test_f10_class_shortcut_multiple_string_args() -> None:
    """Class shortcut Apply.groupby('A', 'B') correctly includes all args."""
    result = Apply.groupby("State", "Priority").build()
    assert result == "$apply=groupby((State,Priority))"


# -----------------------------------------------------------------------
# F12: groupby+aggregate nesting + countdistinct guard
# -----------------------------------------------------------------------


def test_f12_groupby_aggregate_nested_count() -> None:
    """F12 AC-1: aggregate after groupby emits nested form with $count."""
    result = (
        Apply()
        .groupby("DateSK", "State")
        .aggregate("$count", alias="Count")
        .build()
    )
    assert result == "$apply=groupby((DateSK,State),aggregate($count as Count))"


def test_f12_filter_groupby_aggregate_nested() -> None:
    """F12 AC-2: filter standalone + nested groupby/aggregate."""
    result = (
        Apply()
        .filter(Filter.eq("StateCategory", "Completed"))
        .groupby("DateSK", "State")
        .aggregate("$count", alias="Count")
        .build()
    )
    assert result == (
        "$apply=filter(StateCategory eq 'Completed')"
        "/groupby((DateSK,State),aggregate($count as Count))"
    )


def test_f12_standalone_aggregate_unchanged() -> None:
    """F12 AC-3: standalone aggregate (no groupby) keeps top-level form."""
    result = Apply().aggregate("$count", alias="Count").build()
    assert result == "$apply=aggregate($count as Count)"


def test_f12_countdistinct_blocked() -> None:
    """F12 AC-4a: countdistinct is rejected at DSL call time (instance)."""
    with pytest.raises(NotImplementedError, match="countdistinct"):
        Apply().aggregate("WorkItemId", "countdistinct")


def test_f12_countdistinct_blocked_class_shortcut() -> None:
    """F12 AC-4b: countdistinct rejected at class level too."""
    with pytest.raises(NotImplementedError, match="countdistinct"):
        Apply.aggregate("WorkItemId", "countdistinct")


def test_f12_countdistinct_error_message() -> None:
    """F12 AC-4c: countdistinct error message includes MS Learn URL and explanation."""
    with pytest.raises(NotImplementedError) as exc_info:
        Apply().aggregate("WorkItemId", "countdistinct")
    msg = str(exc_info.value)
    assert "countdistinct" in msg
    assert (
        "https://learn.microsoft.com/en-us/azure/devops/report/extend-analytics/odata-query-guidelines"
        in msg
    )
    assert "$count" in msg
    assert "sum/min/max/avg" in msg


def test_f12_class_shortcut_with_alias_no_crash() -> None:
    """Class shortcut Apply.aggregate('$count', alias='Count') must NOT crash."""
    result = Apply.aggregate("$count", alias="Count").build()
    assert result == "$apply=aggregate($count as Count)"


def test_f12_class_shortcut_single_arg_raises_value_error() -> None:
    """Class shortcut Apply.aggregate('field') with single arg raises ValueError."""
    with pytest.raises(ValueError, match="requires a method argument"):
        Apply.aggregate("field")  # type: ignore[call-arg]  # reason: intentionally testing the guard
