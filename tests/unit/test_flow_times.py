"""Tests for SPEC-017: State transitions & flow times computation."""

from __future__ import annotations

from datetime import date

from ado_odata_async.flow_times import compute_flow_times


def _rev(state: str, changed: str) -> dict[str, str]:
    return {"State": state, "ChangedDate": changed}


class TestAC1StateHistory:
    def test_builds_chronological_history(self) -> None:
        revisions = [
            _rev("New", "2026-01-01"),
            _rev("Active", "2026-01-05"),
            _rev("Resolved", "2026-01-10"),
        ]
        result = compute_flow_times(revisions)
        assert result.state_history == [
            ("New", date(2026, 1, 1)),
            ("Active", date(2026, 1, 5)),
            ("Resolved", date(2026, 1, 10)),
        ]


class TestAC2TimeInQueue:
    def test_queue_time_calculated(self) -> None:
        revisions = [
            _rev("New", "2026-01-01"),
            _rev("Active", "2026-01-08"),
        ]
        result = compute_flow_times(revisions)
        assert result.time_in_queue_days == 7

    def test_single_state_no_queue(self) -> None:
        revisions = [_rev("Active", "2026-01-01")]
        result = compute_flow_times(revisions)
        assert result.time_in_queue_days == 0


class TestAC3TimeInProgress:
    def test_multiple_periods(self) -> None:
        revisions = [
            _rev("New", "2026-01-01"),
            _rev("Active", "2026-01-08"),
            _rev("New", "2026-01-15"),
            _rev("Active", "2026-01-20"),
            _rev("Closed", "2026-01-25"),
        ]
        result = compute_flow_times(revisions)
        assert result.time_in_progress_days == 12

    def test_single_period(self) -> None:
        revisions = [
            _rev("New", "2026-01-01"),
            _rev("Active", "2026-01-08"),
            _rev("Closed", "2026-01-15"),
        ]
        result = compute_flow_times(revisions)
        assert result.time_in_progress_days == 7


class TestAC4StillInQueue:
    def test_never_active(self) -> None:
        revisions = [
            _rev("New", "2026-01-01"),
            _rev("New", "2026-01-05"),
        ]
        result = compute_flow_times(revisions)
        assert result.time_in_queue_days is None
        assert result.time_in_progress_days == 0

    def test_empty_revisions(self) -> None:
        result = compute_flow_times([])
        assert result.time_in_queue_days is None
        assert result.time_in_progress_days == 0
        assert result.state_history == []
