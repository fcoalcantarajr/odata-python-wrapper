"""Tests for SPEC-014: Plan history & on-time rate computation."""

from __future__ import annotations

from datetime import date

from ado_odata_async.plan_history import compute_plan_history


def _make_item(
    wid: int,
    created: str,
    state_category: str = "In Progress",
    completed: str | None = None,
    target: str | None = None,
) -> dict[str, object]:
    return {
        "WorkItemId": wid,
        "CreatedDate": created,
        "StateCategory": state_category,
        "CompletedDate": completed,
        "TargetDate": target,
    }


class TestAC1CreatedDate:
    def test_returns_minimum_created_date(self) -> None:
        items = [
            _make_item(1, "2026-01-15"),
            _make_item(2, "2026-01-10"),
            _make_item(3, "2026-01-20"),
        ]
        result = compute_plan_history(items)
        assert result.created_date == date(2026, 1, 10)

    def test_single_item(self) -> None:
        items = [_make_item(1, "2026-03-01")]
        result = compute_plan_history(items)
        assert result.created_date == date(2026, 3, 1)


class TestAC2OldestCardDate:
    def test_returns_min_created_of_active_items(self) -> None:
        items = [
            _make_item(1, "2026-01-01", "Completed"),
            _make_item(2, "2026-01-05", "In Progress"),
            _make_item(3, "2026-01-10", "New"),
        ]
        result = compute_plan_history(items)
        assert result.oldest_card_date == date(2026, 1, 5)

    def test_all_completed_returns_none(self) -> None:
        items = [
            _make_item(1, "2026-01-01", "Completed"),
            _make_item(2, "2026-01-05", "Completed"),
        ]
        result = compute_plan_history(items)
        assert result.oldest_card_date is None


class TestAC3OnTimeRate:
    def test_all_on_time(self) -> None:
        items = [
            _make_item(1, "2026-01-01", "Completed", "2026-02-01", "2026-02-05"),
            _make_item(2, "2026-01-01", "Completed", "2026-02-03", "2026-02-05"),
        ]
        result = compute_plan_history(items)
        assert result.on_time_rate == 1.0

    def test_some_late(self) -> None:
        items = [
            _make_item(1, "2026-01-01", "Completed", "2026-02-01", "2026-02-05"),
            _make_item(2, "2026-01-01", "Completed", "2026-02-10", "2026-02-05"),
        ]
        result = compute_plan_history(items)
        assert result.on_time_rate == 0.5

    def test_no_completed_items(self) -> None:
        items = [_make_item(1, "2026-01-01", "In Progress")]
        result = compute_plan_history(items)
        assert result.on_time_rate == 0.0


class TestAC4EmptyItems:
    def test_empty_list(self) -> None:
        result = compute_plan_history([])
        assert result.created_date is None
        assert result.oldest_card_date is None
        assert result.on_time_rate == 0.0


class TestAC5MissingTargetDate:
    def test_skips_items_without_target(self) -> None:
        items = [
            _make_item(1, "2026-01-01", "Completed", "2026-02-01", "2026-02-05"),
            _make_item(2, "2026-01-01", "Completed", "2026-02-10", None),
        ]
        result = compute_plan_history(items)
        assert result.on_time_rate == 1.0


class TestISODateTimeFormat:
    def test_handles_datetime_with_time_component(self) -> None:
        items = [
            _make_item(1, "2026-01-15T00:00:00Z", "In Progress"),
            _make_item(2, "2026-01-10T12:30:00Z", "Completed", "2026-02-01", "2026-02-05"),
        ]
        result = compute_plan_history(items)
        assert result.created_date == date(2026, 1, 10)

    def test_handles_mixed_formats(self) -> None:
        items = [
            _make_item(1, "2026-01-15T00:00:00Z", "In Progress"),
            _make_item(2, "2026-01-10", "Completed", "2026-02-01", "2026-02-05"),
        ]
        result = compute_plan_history(items)
        assert result.created_date == date(2026, 1, 10)
