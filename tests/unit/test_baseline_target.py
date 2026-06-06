"""Tests for SPEC-016: Baseline vs current target date computation."""

from __future__ import annotations

from ado_odata_async.baseline_target import compute_baseline_metrics


def _revision(target_date: str | None, rev_id: int = 1) -> dict[str, object]:
    return {"TargetDate": target_date, "Rev": rev_id}


class TestAC1OriginalTargetDate:
    def test_extracts_first_target_date(self) -> None:
        revisions = [
            _revision("2026-03-15", 1),
            _revision("2026-04-01", 2),
            _revision("2026-04-10", 3),
        ]
        result = compute_baseline_metrics(revisions)
        assert result.original_target_date == "2026-03-15"

    def test_single_revision(self) -> None:
        revisions = [_revision("2026-06-01", 1)]
        result = compute_baseline_metrics(revisions)
        assert result.original_target_date == "2026-06-01"


class TestAC2TargetDateChanges:
    def test_no_changes(self) -> None:
        revisions = [_revision("2026-03-15", 1)]
        result = compute_baseline_metrics(revisions)
        assert result.target_date_changes == 0

    def test_two_changes(self) -> None:
        revisions = [
            _revision("2026-03-15", 1),
            _revision("2026-04-01", 2),
            _revision("2026-04-10", 3),
        ]
        result = compute_baseline_metrics(revisions)
        assert result.target_date_changes == 2


class TestAC3ReplannedFlag:
    def test_replanned_true(self) -> None:
        revisions = [
            _revision("2026-03-15", 1),
            _revision("2026-04-01", 2),
        ]
        result = compute_baseline_metrics(revisions)
        assert result.replanned is True

    def test_replanned_false(self) -> None:
        revisions = [_revision("2026-03-15", 1)]
        result = compute_baseline_metrics(revisions)
        assert result.replanned is False


class TestAC4NoTargetDate:
    def test_all_none(self) -> None:
        revisions = [_revision(None, 1), _revision(None, 2)]
        result = compute_baseline_metrics(revisions)
        assert result.original_target_date is None
        assert result.target_date_changes == 0
        assert result.replanned is False

    def test_empty_revisions(self) -> None:
        result = compute_baseline_metrics([])
        assert result.original_target_date is None
        assert result.target_date_changes == 0
        assert result.replanned is False
