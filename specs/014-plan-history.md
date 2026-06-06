<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# SPEC-014: Plan History & On-Time Rate

- id: SPEC-014
- slug: plan-history
- status: DRAFT
- created: 2026-06-05
- owner: @sisyphus

## User Story

As a delivery lead, I want to compute plan history metrics (created date, oldest card, on-time rate) from work item data, so that I can assess delivery predictability and identify stale work.

## Use Cases

- UC1: Compute `created_date` (earliest creation timestamp) for a set of work items
- UC2: Compute `oldest_card_date` (most recent creation date among oldest active cards)
- UC3: Compute `on_time_rate` (percentage of completed items delivered before target date)
- UC4: Handle empty work item sets gracefully (return None/0.0)

## Acceptance Criteria (Gherkin absoluto)

### AC-1: Compute created_date

```
Given a list of work items with CreatedDate fields
When I call compute_plan_history with those items
Then the result contains created_date equal to the minimum CreatedDate value
```

### AC-2: Compute oldest_card_date

```
Given a list of work items including active (StateCategory != Completed) items
When I call compute_plan_history with those items
Then the result contains oldest_card_date equal to the maximum CreatedDate among active items
```

### AC-3: Compute on_time_rate

```
Given a list of work items with CompletedDate and TargetDate fields
When I call compute_plan_history with those items
Then the result contains on_time_rate equal to count of items where CompletedDate <= TargetDate divided by total completed items count
```

### AC-4: Handle empty work items

```
Given an empty list of work items
When I call compute_plan_history with those items
Then the result contains created_date as None, oldest_card_date as None, and on_time_rate as 0.0
```

### AC-5: Handle items without TargetDate

```
Given a list of work items where some completed items lack TargetDate
When I call compute_plan_history with those items
Then the result contains on_time_rate calculated only from items that have TargetDate
```

## NFRs

- **Performance:** Computation completes in O(n) time where n is number of work items
- **Security:** No PAT handling (pure computation on already-fetched data)
- **Observability:** N/A (synchronous utility function)

## INVEST self-score

- **I**ndependent: 9/10 — Pure computation, no external dependencies
- **N**egotiable: 8/10 — Metrics definitions could vary
- **V**aluable: 9/10 — Core metrics for delivery plan analysis
- **E**stimable: 9/10 — Clear input/output specification
- **S**mall: 9/10 — Single function with helpers
- **T**estable: 10/10 — Deterministic input/output

Média: 9.0/10 (APPROVED)

## Out-of-scope

- Network calls or data fetching (assumes data already fetched)
- Time-based filtering or date range queries
- Visualization or reporting

## Test plan

- AC-1 → `tests/unit/test_plan_history.py::test_ac1_created_date`
- AC-2 → `tests/unit/test_plan_history.py::test_ac2_oldest_card_date`
- AC-3 → `tests/unit/test_plan_history.py::test_ac3_on_time_rate`
- AC-4 → `tests/unit/test_plan_history.py::test_ac4_empty_items`
- AC-5 → `tests/unit/test_plan_history.py::test_ac5_missing_target_date`

## DoD

- [ ] Todos AC verdes em `uv run pytest -q tests/unit/test_plan_history.py`
- [ ] Coverage do módulo tocado ≥ 85%
- [ ] `ruff check .`, `mypy src/` exit 0
- [ ] `bash scripts/audit.sh` exit 0
- [ ] HARD RULES respeitadas: HR-3 (test first), HR-24 (functions ≤50 lines, ≤5 params)
- [ ] Conventional Commit emitido por `git-keeper` referenciando `(SPEC-014)`
