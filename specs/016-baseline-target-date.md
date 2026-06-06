<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# SPEC-016: Baseline vs Current Target Date

- id: SPEC-016
- slug: baseline-target-date
- status: DRAFT
- created: 2026-06-05
- owner: @sisyphus

## User Story

As a delivery lead, I want to detect target date changes (replanning) from work item revision history, so that I can assess delivery predictability and replanning frequency.

## Use Cases

- UC1: Extract `original_target_date` from earliest revision with a target date
- UC2: Count `target_date_changes` (number of times target date was modified)
- UC3: Set `replanned` flag when target date changed after initial baseline
- UC4: Handle work items with no target date in any revision

## Acceptance Criteria (Gherkin absoluto)

### AC-1: Extract original_target_date

```
Given a list of revisions ordered by date with TargetDate fields
When I call compute_baseline_metrics with those revisions
Then the result contains original_target_date equal to the first TargetDate value
```

### AC-2: Count target_date_changes

```
Given a list of revisions where TargetDate changed 3 times
When I call compute_baseline_metrics with those revisions
Then the result contains target_date_changes equal to 2 (baseline to first change = 1, then 2 more = total 2 changes after baseline)
```

### AC-3: Set replanned flag

```
Given a list of revisions where TargetDate changed at least once after baseline
When I call compute_baseline_metrics with those revisions
Then the result contains replanned as True
```

### AC-4: Handle no target date

```
Given a list of revisions where no revision has a TargetDate
When I call compute_baseline_metrics with those revisions
Then the result contains original_target_date as None, target_date_changes as 0, and replanned as False
```

## NFRs

- **Performance:** O(n) time where n is number of revisions
- **Security:** Pure computation on already-fetched data
- **Observability:** N/A (synchronous utility function)

## INVEST self-score

- **I**ndependent: 9/10 — Pure computation on revision data
- **N**egotiable: 8/10 — Change counting semantics could vary
- **V**aluable: 9/10 — Core metric for replanning analysis
- **E**stimable: 9/10 — Clear input/output specification
- **S**mall: 9/10 — Single focused function
- **T**estable: 10/10 — Deterministic input/output

Média: 9.0/10 (APPROVED)

## Out-of-scope

- Revision fetching (assumes data already fetched)
- Target date comparison with actual completion
- Historical trend analysis

## Test plan

- AC-1 → `tests/unit/test_baseline_target.py::test_ac1_original_target_date`
- AC-2 → `tests/unit/test_baseline_target.py::test_ac2_target_date_changes`
- AC-3 → `tests/unit/test_baseline_target.py::test_ac3_replanned_flag`
- AC-4 → `tests/unit/test_baseline_target.py::test_ac4_no_target_date`

## DoD

- [ ] Todos AC verdes em `uv run pytest -q tests/unit/test_baseline_target.py`
- [ ] Coverage do módulo tocado ≥ 85%
- [ ] `ruff check .`, `mypy src/` exit 0
- [ ] `bash scripts/audit.sh` exit 0
- [ ] HARD RULES respeitadas: HR-3 (test first), HR-24 (functions ≤50 lines)
- [ ] Conventional Commit emitido por `git-keeper` referenciando `(SPEC-016)`
