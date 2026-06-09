<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# SPEC-017: State Transitions & Flow Times

- id: SPEC-017
- slug: state-transitions-flow-times
- status: IMPLEMENTED
- created: 2026-06-05
- owner: @sisyphus

## User Story

As a delivery lead, I want to compute state transition history and flow times (queue time, progress time) from work item revisions, so that I can identify bottlenecks and measure delivery velocity.

## Use Cases

- UC1: Build `state_history` — ordered list of (state, entered_at) tuples from revisions
- UC2: Compute `time_in_queue_days` — duration from creation to first "In Progress" state
- UC3: Compute `time_in_progress_days` — total duration in "In Progress" / active states
- UC4: Handle items that never left the initial state (still in queue)

## Acceptance Criteria (Gherkin absoluto)

### AC-1: Build state_history

```
Given a list of revisions with State and ChangedDate fields
When I call compute_flow_times with those revisions
Then the result contains state_history as a list of (state, date) tuples in chronological order
```

### AC-2: Compute time_in_queue_days

```
Given revisions where the item was created on 2026-01-01 and moved to In Progress on 2026-01-08
When I call compute_flow_times with those revisions
Then the result contains time_in_queue_days equal to 7
```

### AC-3: Compute time_in_progress_days

```
Given revisions where the item was In Progress from 2026-01-08 to 2026-01-15 and 2026-01-20 to 2026-01-25
When I call compute_flow_times with those revisions
Then the result contains time_in_progress_days equal to 12
```

### AC-4: Handle items still in queue

```
Given revisions where the item was never moved to an active state
When I call compute_flow_times with those revisions
Then the result contains time_in_queue_days as None and time_in_progress_days as 0
```

## NFRs

- **Performance:** O(n) time where n is number of revisions
- **Security:** Pure computation on already-fetched data
- **Observability:** N/A (synchronous utility function)

## INVEST self-score

- **I**ndependent: 9/10 — Pure computation on revision data
- **N**egotiable: 8/10 — Active state definition could vary
- **V**aluable: 9/10 — Core metrics for flow analysis
- **E**stimable: 9/10 — Clear input/output specification
- **S**mall: 9/10 — Single focused function
- **T**estable: 10/10 — Deterministic input/output

Média: 9.0/10 (APPROVED)

## Out-of-scope

- Revision fetching (assumes data already fetched)
- Cycle time computation (covered by existing cookbook)
- Throughput / WIP metrics

## Test plan

- AC-1 → `tests/unit/test_flow_times.py::test_ac1_state_history`
- AC-2 → `tests/unit/test_flow_times.py::test_ac2_time_in_queue`
- AC-3 → `tests/unit/test_flow_times.py::test_ac3_time_in_progress`
- AC-4 → `tests/unit/test_flow_times.py::test_ac4_still_in_queue`

## DoD

- [ ] Todos AC verdes em `uv run pytest -q tests/unit/test_flow_times.py`
- [ ] Coverage do módulo tocado ≥ 85%
- [ ] `ruff check .`, `mypy src/` exit 0
- [ ] `bash scripts/audit.sh` exit 0
- [ ] HARD RULES respeitadas: HR-3 (test first), HR-24 (functions ≤50 lines)
- [ ] Conventional Commit emitido por `git-keeper` referenciando `(SPEC-017)`
