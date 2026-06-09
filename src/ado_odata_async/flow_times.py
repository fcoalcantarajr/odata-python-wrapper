"""State transitions & flow times — compute from work item revision history."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

ACTIVE_STATES = frozenset({"Active", "In Progress", "Committed", "Design"})


@dataclass(frozen=True, slots=True)
class FlowTimeResult:
    """Flow time metrics computed from work item revision history.

    Attributes:
        state_history: Chronologically sorted list of (State, ChangedDate)
            tuples extracted from revisions. Empty if no valid revisions.
        time_in_queue_days: Days from creation (first revision) to first
            transition into an active state (Active, In Progress, Committed,
            Design). None if never entered an active state.
        time_in_progress_days: Total days spent in active states. Sums
            durations of contiguous active-state periods. 0 if never active.
    """

    state_history: list[tuple[str, date]] = field(default_factory=list)
    time_in_queue_days: int | None = None
    time_in_progress_days: int = 0


def compute_flow_times(revisions: list[dict[str, Any]]) -> FlowTimeResult:
    """Compute state transition history and flow times from revision history.

    Parses revisions for State and ChangedDate, builds a sorted timeline,
    then calculates:
    - Queue time: days from creation to first active state
    - Progress time: total days spent in active states

    Args:
        revisions: List of revision dicts with "State" and "ChangedDate"
            keys. ChangedDate should be ISO 8601 string (with or without
            time component).

    Returns:
        FlowTimeResult with state_history, time_in_queue_days, and
        time_in_progress_days.
    """
    if not revisions:
        return FlowTimeResult()

    history: list[tuple[str, date]] = []
    for rev in revisions:
        state = rev.get("State", "")
        changed = rev.get("ChangedDate")
        if changed is not None:
            try:
                date_part = changed[:10] if isinstance(changed, str) and "T" in changed else changed
                history.append((state, date.fromisoformat(date_part)))
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
