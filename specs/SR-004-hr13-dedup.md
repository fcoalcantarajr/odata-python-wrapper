<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# SR-004: Deduplicate HR-13 (Snapshot groupby) validation into single function

- id: SR-004
- slug: hr13-dedup
- status: DRAFT
- created: 2026-05-27
- owner: sisyphus
- findings-addressed: SR-004

## User Story

As a maintainer of the query module, I want HR-13 validation to live in exactly one place,
so that updating the GroupBy syntax for Snapshot entities doesn't require editing 3 files
with copy-pasted regex patterns.

## Use Cases

- UC1: Any caller needing HR-13 validation calls the same shared function
- UC2: `Apply.validate()` delegates to the shared function when entity_type is set
- UC3: `QueryBuilder.apply()` delegates to the shared function
- UC4: `QueryBuilder._validate_hr13()` delegates to the shared function
- UC5: Non-snapshot entity sets are unaffected (no validation overhead)

## Acceptance Criteria (Gherkin absoluto)

### AC-1: Shared function exists and validates WorkItemSnapshot

```
Given the shared HR-13 validation function
When called with entity_set="WorkItemSnapshot" and apply_value="groupby((DateSK))"
Then it returns None (no error)
```

### AC-2: Shared function rejects missing DateSK

```
Given the shared HR-13 validation function
When called with entity_set="WorkItemSnapshot" and apply_value="groupby((State))"
Then it raises ValueError with message containing "DateSK"
```

### AC-3: Shared function validates WorkItemBoardSnapshot

```
Given the shared HR-13 validation function
When called with entity_set="WorkItemBoardSnapshot" and apply_value="groupby((DateValue))"
Then it returns None (no error)
```

### AC-4: Shared function rejects missing DateValue

```
Given the shared HR-13 validation function
When called with entity_set="WorkItemBoardSnapshot" and apply_value="groupby((State))"
Then it raises ValueError with message containing "DateValue"
```

### AC-5: Non-snapshot entity sets pass through

```
Given the shared HR-13 validation function
When called with entity_set="WorkItems" and apply_value=""
Then it returns None (no error)
```

### AC-6: All three original call sites delegate to the shared function

```
Given Apply(entity_type="WorkItemSnapshot").groupby("DateSK")
When .validate() is called
Then no ValueError is raised (delegates to shared function)
```

```
Given QueryBuilder with entity_set="WorkItemSnapshot"
When .apply(Apply.groupby("DateSK")) is called
Then no ValueError is raised (delegates to shared function)
```

```
Given QueryBuilder with entity_set="WorkItemBoardSnapshot" and no $apply
When ._validate_hr13() is called
Then ValueError is raised (delegates to shared function)
```

### AC-7: Regex pattern exists exactly once in the codebase

```
Given the shared HR-13 validation function is defined in src/
When searching src/ for the exact regex literal r"groupby\(\(([^)]+)\)\)"
Then the pattern appears exactly once (inside the shared function definition)
```

## NFRs

- **Performance:** Shared function adds < 1µs overhead for non-snapshot entity sets (early return)
- **Maintainability:** Regex pattern must be zero copy-paste instances outside the shared function

## INVEST self-score

- **I**ndependent: 10/10 — no external dependencies
- **N**egotiable: 7/10 — exact location of shared function is negotiable (utility module vs. inline)
- **V**aluable: 9/10 — copy-paste debt is a known maintenance risk
- **E**stimable: 10/10 — extract function, update 3 callers, run tests
- **S**mall: 10/10 — < 50 lines of code change
- **T**estable: 10/10 — pure function, easily unit-tested

Média: 9.3/10

## Out-of-scope

- Changing the HR-13 validation logic itself (still requires groupby(DateSK/DateValue))
- Adding validation for other HARD RULES
- Renaming the regex pattern location semantics

## Test plan

- AC-1 → `tests/unit/test_sr_004_hr13_dedup.py::test_ac1_valid_workitem_snapshot`
- AC-2 → `tests/unit/test_sr_004_hr13_dedup.py::test_ac2_missing_datesk`
- AC-3 → `tests/unit/test_sr_004_hr13_dedup.py::test_ac3_valid_board_snapshot`
- AC-4 → `tests/unit/test_sr_004_hr13_dedup.py::test_ac4_missing_datevalue`
- AC-5 → `tests/unit/test_sr_004_hr13_dedup.py::test_ac5_non_snapshot_passthrough`
- AC-6 → `tests/unit/test_sr_004_hr13_dedup.py::test_ac6_apply_validate_delegates`
- AC-7 → `scripts/audit.sh` update or `grep` check in CI

## Hard Rules

- HR-13 (enforcement preserved — must still block non-groupby Snapshot queries)
