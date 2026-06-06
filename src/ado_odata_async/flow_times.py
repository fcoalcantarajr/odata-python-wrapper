"""State transitions & flow times — compute from work item revision history."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

ACTIVE_STATES = frozenset({"Active", "In Progress", "Committed", "Design"})


@dataclass(frozen=True, slots=True)
class FlowTimeResult:
    state_history: list[tuple[str, date]] = field(default_factory=list)
    time_in_queue_days: int | None = None
    time_in_progress_days: int = 0


def compute_flow_times(revisions: list[dict[str, Any]]) -> FlowTimeResult:
    if not revisions:
        return FlowTimeResult()

    history: list[tuple[str, date]] = []
    for rev in revisions:
        state = rev.get("State", "")
        changed = rev.get("ChangedDate")
        if changed is not None:
            try:
                history.append((state, date.fromisoformat(changed)))
            except (ValueError, TypeError):
                continue

    if not history:
        return FlowTimeResult()

    history.sort(key=lambda x: x[1])

    created_date = history[0][1]
    queue_days: int | None = None
    progress_days = 0

    first_active_idx: int | None = None
    for i, (state, dt) in enumerate(history):
        if state in ACTIVE_STATES and first_active_idx is None:
            first_active_idx = i
            queue_days = (dt - created_date).days
            break

    if first_active_idx is not None:
        active_start: date | None = None
        for i in range(first_active_idx, len(history)):
            state, dt = history[i]
            if state in ACTIVE_STATES:
                if active_start is None:
                    active_start = dt
            else:
                if active_start is not None:
                    progress_days += (dt - active_start).days
                    active_start = None

        if active_start is not None:
            progress_days += (history[-1][1] - active_start).days

    return FlowTimeResult(history, queue_days, progress_days)
