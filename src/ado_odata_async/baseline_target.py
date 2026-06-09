"""Baseline target date — detect replanning from revision history."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class BaselineResult:
    """Target date baseline detection result from revision history.

    Attributes:
        original_target_date: The first TargetDate value encountered in
            the revision sequence (chronological order). None if no
            revisions have a TargetDate.
        target_date_changes: Count of times TargetDate changed between
            consecutive revisions. Only counts actual value changes.
        replanned: True if target_date_changes > 0, indicating the
            target date was modified at least once after initial set.
    """

    original_target_date: str | None
    target_date_changes: int
    replanned: bool


def compute_baseline_metrics(revisions: list[dict[str, Any]]) -> BaselineResult:
    """Detect target date replanning from work item revision history.

    Extracts TargetDate values from revisions in order, identifies the
    original target date, and counts how many times it changed.

    Args:
        revisions: List of revision dicts with optional "TargetDate"
            key. Expected in chronological order (oldest first).

    Returns:
        BaselineResult with original_target_date, target_date_changes,
        and replanned flag.
    """
    if not revisions:
        return BaselineResult(None, 0, False)

    target_dates = [rev.get("TargetDate") for rev in revisions if rev.get("TargetDate") is not None]

    if not target_dates:
        return BaselineResult(None, 0, False)

    original = target_dates[0]
    changes = sum(1 for i in range(1, len(target_dates)) if target_dates[i] != target_dates[i - 1])

    return BaselineResult(original, changes, changes > 0)
