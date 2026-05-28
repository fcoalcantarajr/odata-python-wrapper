<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# AS-101 — Fix snapshot groupby regex to match nested aggregate expressions

- id: AS-101
- slug: snapshot-groupby-regex
- status: APPROVED
- created: 2026-05-28
- owner: sisyphus
- findings-addressed: AS-101

## User Story

As a user querying WorkItemSnapshot with aggregated metrics,
I want the `_check_snapshot_groupby` regex to correctly match `groupby((DateSK),aggregate(...))` patterns with nested parentheses,
so that valid `$apply` expressions combining groupby and aggregate over snapshot entities are not falsely rejected by HR-13 validation.

## Use Cases

- UC1: `$apply=groupby((DateSK),aggregate(Count with sum as Total))` for WorkItemSnapshot must pass validation
- UC2: Simple `$apply=groupby((DateSK))` must still work (backward compat)
- UC3: Missing DateSK in groupby fields must still raise ValueError
- UC4: `$apply=groupby((DateValue),aggregate(Effort with sum as Effort))` for WorkItemBoardSnapshot must pass
- UC5: Non-snapshot entity (e.g. WorkItems) with any $apply must be silently skipped

## Acceptance Criteria (Gherkin absoluto)

### AC-1: Nested groupby + aggregate passes for WorkItemSnapshot

```
Given a WorkItemSnapshot entity set
When _check_snapshot_groupby is called with apply_value="groupby((DateSK),aggregate(Count with sum as Total))"
Then no exception is raised
```

### AC-2: Simple groupby still works

```
Given a WorkItemSnapshot entity set
When _check_snapshot_groupby is called with apply_value="groupby((DateSK))"
Then no exception is raised
```

### AC-3: Missing DateSK in nested form raises ValueError

```
Given a WorkItemSnapshot entity set
When _check_snapshot_groupby is called with apply_value="groupby((State),aggregate(Count with sum as Total))"
Then a ValueError is raised with message containing "requires groupby(DateSK)"
```

### AC-4: Missing DateSK in simple form raises ValueError

```
Given a WorkItemSnapshot entity set
When _check_snapshot_groupby is called with apply_value="groupby((State))"
Then a ValueError is raised with message containing "requires groupby(DateSK)"
```

### AC-5: Non-snapshot entity is silently skipped

```
Given a WorkItems entity set (not a snapshot)
When _check_snapshot_groupby is called with any apply_value
Then the function returns None
```

### AC-6: Board snapshot with DateValue + aggregate passes

```
Given a WorkItemBoardSnapshot entity set
When _check_snapshot_groupby is called with apply_value="groupby((DateValue),aggregate(Effort with sum as Effort))"
Then no exception is raised
```

### AC-7: Regex captures only outer groupby fields

```
Given the regex pattern r"groupby\(\(([^)]+)\)"
When applied to "groupby((DateSK,State),aggregate(...))"
Then group(1) equals "DateSK,State"
```

### AC-8: Deeply nested aggregate functions pass

```
Given a WorkItemSnapshot entity set
When _check_snapshot_groupby is called with apply_value="groupby((DateSK),aggregate(SomeFunction(p1,p2) with sum as Total))"
Then no exception is raised
```

## Root Cause & Fix

- **Bug** (line 282): `r"groupby\(\(([^)]+)\)\)"` — `[^)]+` cannot match `)` characters, so the trailing `\)` is unreachable for any nested aggregate expression
- **Fix**: `r"groupby\(\(([^)]+)\)"` — remove the trailing `\)` so it matches up to the *outer* closing paren only
- **Location**: `src/ado_odata_async/query/_apply.py:282`

## INVEST self-score

- **I**ndependent: 10/10 — single-file fix, no dependencies
- **N**egotiable: 9/10 — exact regex is negotiable, ACs are fixed
- **V**aluable: 10/10 — unblocks ALL snapshot+aggregate queries
- **E**stimable: 10/10 — one-char regex fix + tests; <30 min
- **S**mall: 10/10 — changes exactly 1 production line + tests
- **T**estable: 10/10 — pure function, direct assertions

Média: 9.8/10

## Out of scope

- Full OData $apply parser (ANTLR/PEG)
- Nested groupby inside filter or other expressions
- Changes to Apply builder class or its fluent API
- HR-13 for entity sets beyond WorkItemSnapshot/WorkItemBoardSnapshot

## Test plan

- AC-1 → test_nested_groupby_aggregate_passes
- AC-2 → test_simple_groupby_still_passes
- AC-3 → test_missing_required_nested_raises
- AC-4 → test_missing_required_simple_raises
- AC-5 → test_non_snapshot_entity_skipped
- AC-6 → test_board_snapshot_datevalue_aggregate_passes
- AC-7 → test_regex_extracts_outer_fields_only
- AC-8 → test_deeply_nested_aggregates_pass

## DoD

- [ ] AC-1 a AC-8 verdes
- [ ] `uv run pytest -q` exit 0
- [ ] `uv run ruff check .` exit 0
- [ ] `uv run mypy src/` exit 0
- [ ] `bash scripts/audit.sh` exit 0
