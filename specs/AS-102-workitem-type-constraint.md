<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# AS-102: Relax WorkItemType to accept custom work item types

- id: AS-102
- slug: workitem-type-constraint
- status: APPROVED
- created: 2026-05-28
- owner: @opencode

## User Story

As a developer using Azure DevOps with a **custom process template** (Initiative, OKR, Spike, Risk),
I want `WorkItemType` to accept **any string value** (logging a warning for non-standard types instead of raising `ValueError`),
so that my ADO projects with custom work item types don't crash the library with a `ValidationError`.

## Background

`src/ado_odata_async/entities/_workitem.py:29` currently defines:

```python
WorkItemType: Literal["Bug", "User Story", "Task", "Feature", "Epic"]
```

with a `field_validator("WorkItemType")` that raises `ValueError` if the value is not in
the `WORK_ITEM_TYPES` tuple. This makes the library **unusable for any ADO project**
that uses a custom process template — a **SEVERE** blocking issue (AS-102).

**Fix scope:**
1. Change `WorkItemType` field type from `Literal[...]` to `str`.
2. Replace the `field_validator` from raising `ValueError` to calling `logger.warning(...)`.
3. Keep `WORK_ITEM_TYPES` tuple as a reference list.

## Use Cases

- **UC1:** Standard work item types ("Bug", "User Story", "Task", "Feature", "Epic") parse without errors or warnings.
- **UC2:** Non-standard work item types ("Initiative", "OKR", "Spike", "Risk") parse successfully; a warning is emitted via the module logger.
- **UC3:** A `WorkItem` with a custom type is fully usable — all fields accessible, model is frozen+strict, type is preserved as-is.

## Acceptance Criteria (Gherkin absoluto)

### AC-1: Standard WorkItemType parses without error

```
Given a WorkItem JSON row with WorkItemType="Bug"
When WorkItem.model_validate(row) is called
Then no exception is raised
  And the resulting WorkItemType equals "Bug"
```

### AC-2: Custom WorkItemType parses without ValidationError

```
Given a WorkItem JSON row with WorkItemType="Initiative"
When WorkItem.model_validate(row) is called
Then no ValidationError is raised
  And the resulting WorkItemType equals "Initiative"
```

### AC-3: Custom WorkItemType emits a logger warning

```
Given a WorkItem JSON row with WorkItemType="OKR"
And a caplog fixture capturing logging at WARNING level
When WorkItem.model_validate(row) is called
Then caplog contains a WARNING message matching "WorkItemType.*OKR.*not in standard set"
```

### AC-4: Multiple custom types all succeed

```
Given a list of non-standard types ["Initiative", "OKR", "Spike", "Risk"]
When WorkItem.model_validate is called for each type
Then ValidationError is never raised
  And each parsed WorkItemType matches the input string exactly
```

### AC-5: Standard type emits no logger warning

```
Given a WorkItem JSON row with WorkItemType="Bug"
And a caplog fixture capturing logging at WARNING level
When WorkItem.model_validate(row) is called
Then caplog contains no WARNING messages matching "not in standard set"
```

### AC-6: Frozen+strict model contract is preserved for custom types

```
Given a WorkItem instance with WorkItemType="Initiative"
When attempting to assign instance.WorkItemType = "Spike"
Then TypeError is raised (frozen model)
  And extra fields are still forbidden (extra="forbid")
```

### AC-7: Custom type string is preserved verbatim

```
Given a WorkItem JSON row with WorkItemType="MyOrg__Initiative_v2"
When WorkItem.model_validate(row) is called
Then instance.WorkItemType == "MyOrg__Initiative_v2"
  And type(instance.WorkItemType) is str
```

## NFRs

- **Performance:** Model instantiation with custom type is identical in cost to standard type — no extra I/O, no regex, just a string field + a single in-check against a tuple.
- **Security:** Warning message logs the type value but never the PAT; `WORK_ITEM_TYPES` tuple remains a public constant; no sensitive data leaked.
- **Observability:** Warning is logged at `WARNING` level via the module logger (`ado_odata_async.entities._workitem`); users can configure log handlers to ignore or escalate this warning.
- **Backward compatibility:** Existing spec SPEC-009 AC-1 (standard types) must continue to pass. Existing AC-2 (extra fields), AC-3 (strict types), AC-5 (frozen) must be unaffected.

## INVEST self-score

- **I**ndependent: 10/10 — Single file change in `entities/_workitem.py`; no dependency on other specs or modules; can be implemented, tested, and released standalone.
- **N**egotiable: 9/10 — The `WORK_ITEM_TYPES` list may grow or become configurable in the future; warning vs. info log level is negotiable; the core decision (accept any string) is non-negotiable.
- **V**aluable: 10/10 — Without this fix, the library is broken for every ADO project with a custom process template — a hard blocker for broad adoption.
- **E**stimable: 9/10 — ~5 line code change in `_workitem.py` + ~80 lines of tests; trivially estimable at < 30 min.
- **S**mall: 10/10 — Single-field type change + one validator logic flip + tests; fits in a single commit.
- **T**estable: 10/10 — All ACs testable via direct `model_validate` calls + `caplog`; no network needed; no mocking required.

Média: 9.7/10

## Out-of-scope

- Making `WORK_ITEM_TYPES` configurable or user-extensible at runtime — future feature if demand arises.
- Adding Pydantic `Enum` or `StrEnum` for work item types — the whole point is to accept arbitrary strings.
- Backporting to a v2.0 branch — HR-19 locks to v4.0-preview.
- Changing `WorkItemType` on other entity models (`WorkItemRevisions`, `WorkItemSnapshot`) — those inherit from `ODataEntity` but use their own field definitions; scope is limited to `WorkItem`.
- Introducing a `WorkItemType` custom type or NewType — no need; plain `str` suffices.

## Test plan

- AC-1 → `tests/unit/test_workitem_type_constraint.py::test_ac1_standard_type_parses`
- AC-2 → `tests/unit/test_workitem_type_constraint.py::test_ac2_custom_type_no_validation_error`
- AC-3 → `tests/unit/test_workitem_type_constraint.py::test_ac3_custom_type_logs_warning`
- AC-4 → `tests/unit/test_workitem_type_constraint.py::test_ac4_multiple_custom_types`
- AC-5 → `tests/unit/test_workitem_type_constraint.py::test_ac5_standard_type_no_warning`
- AC-6 → `tests/unit/test_workitem_type_constraint.py::test_ac6_frozen_strict_preserved`
- AC-7 → `tests/unit/test_workitem_type_constraint.py::test_ac7_custom_type_preserved_verbatim`

## DoD

- [ ] All ACs green in `uv run pytest -q tests/unit/test_workitem_type_constraint.py`
- [ ] Existing SPEC-009 tests continue to pass (`uv run pytest -q tests/unit/test_workitem_entity.py`)
- [ ] Coverage of `entities/_workitem.py` ≥ 85%
- [ ] `ruff check .` exit 0
- [ ] `mypy src/` exit 0 (strict)
- [ ] `bash scripts/audit.sh` exit 0
- [ ] HARD RULES respeitadas: HR-4 (frozen+strict), HR-16 (PAT masked), HR-18 (no git direct)
- [ ] `WorkItemType` field type changed from `Literal[...]` to `str`
- [ ] `field_validator("WorkItemType")` changed from `raise ValueError` to `logger.warning(...)`
- [ ] `WORK_ITEM_TYPES` tuple kept as reference constant (not removed)
- [ ] Conventional Commit emitted by `git-keeper` referencing `(AS-102)`
