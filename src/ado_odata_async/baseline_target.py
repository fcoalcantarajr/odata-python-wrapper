"""Baseline target date — detect replanning from revision history."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class BaselineResult:
    original_target_date: str | None
    target_date_changes: int
    replanned: bool


def compute_baseline_metrics(revisions: list[dict[str, Any]]) -> BaselineResult:
    if not revisions:
        return BaselineResult(None, 0, False)

    target_dates = [rev.get("TargetDate") for rev in revisions if rev.get("TargetDate") is not None]

    if not target_dates:
        return BaselineResult(None, 0, False)

    original = target_dates[0]
    changes = sum(1 for i in range(1, len(target_dates)) if target_dates[i] != target_dates[i - 1])

    return BaselineResult(original, changes, changes > 0)
