"""Plan history — compute delivery metrics from work item data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True, slots=True)
class PlanHistoryResult:
    created_date: date | None
    oldest_card_date: date | None
    on_time_rate: float


def _parse_date(value: str | None) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def compute_plan_history(items: list[dict[str, Any]]) -> PlanHistoryResult:
    if not items:
        return PlanHistoryResult(None, None, 0.0)

    created_dates = [_parse_date(item.get("CreatedDate")) for item in items]
    valid_created = [d for d in created_dates if d is not None]
    created_date = min(valid_created) if valid_created else None

    active_items = [item for item in items if item.get("StateCategory") != "Completed"]
    active_created = [_parse_date(item.get("CreatedDate")) for item in active_items]
    valid_active = [d for d in active_created if d is not None]
    oldest_card_date = min(valid_active) if valid_active else None

    completed = [item for item in items if item.get("StateCategory") == "Completed"]
    with_target = [
        item
        for item in completed
        if item.get("TargetDate") is not None and item.get("CompletedDate") is not None
    ]
    on_time = 0
    for item in with_target:
        completed_date = _parse_date(item["CompletedDate"])
        target_date = _parse_date(item["TargetDate"])
        if completed_date is not None and target_date is not None and completed_date <= target_date:
            on_time += 1
    on_time_rate = on_time / len(with_target) if with_target else 0.0

    return PlanHistoryResult(created_date, oldest_card_date, on_time_rate)
