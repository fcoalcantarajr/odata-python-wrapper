<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# SPEC-009: WorkItem entity — Pydantic frozen+strict model

- id: SPEC-009
- slug: workitem-entity
- status: DRAFT
- created: 2026-05-22
- owner: @opencode

## User Story

As a developer consuming WorkItem data from ADO Analytics, I want a `WorkItem` Pydantic model (frozen+strict, HR-4) that maps OData JSON responses to typed Python objects, so that I get IDE autocomplete, type validation, and early schema drift detection.

## Use Cases

- UC1: WorkItem model with fields from OData $metadata.
- UC2: Parse JSON response row into WorkItem instance.
- UC3: extra="forbid" catches unknown fields (schema drift).
- UC4: Fetch WorkItem by ID via client.get_workitem(id).
- UC5: Test against known ADO schema to detect drift.

## Acceptance Criteria (Gherkin absoluto)

### AC-1: WorkItem has required fields

```
Given OData JSON row for WorkItem
When WorkItem.model_validate(row)
Then instance.WorkItemId is int > 0
  And instance.Title is str
  And instance.WorkItemType in {"Bug", "User Story", "Task", "Feature", "Epic"}
```

### AC-2: extra field raises ValidationError

```
Given OData JSON row with unknown field "FutureField"
When WorkItem.model_validate(row)
Then pydantic.ValidationError é levantado com "Extra inputs are not permitted"
```

### AC-3: strict type enforcement

```
Given OData JSON row with WorkItemId="abc" (string instead of int)
When WorkItem.model_validate(row)
Then pydantic.ValidationError é levantado
```

### AC-4: fetch by ID returns WorkItem

```
Given mock HTTP returns WorkItem JSON for id=42
When client.get_workitem(42)
Then retorna WorkItem com WorkItemId=42
```

### AC-5: frozen=True impede mutation

```
Given WorkItem instance
When instance.Title = "new"
Then TypeError é levantado (frozen)
```

## INVEST self-score

Média: 8.7/10

## Test plan

- AC-1 → `test_workitem_entity.py::test_ac1_required_fields`
- AC-2 → `test_workitem_entity.py::test_ac2_extra_field_rejected`
- AC-3 → `test_workitem_entity.py::test_ac3_strict_type_enforcement`
- AC-4 → `test_workitem_entity.py::test_ac4_fetch_by_id`
- AC-5 → `test_workitem_entity.py::test_ac5_frozen_prevents_mutation`

## DoD

- [ ] Todos AC verdes
- [ ] Coverage de `entities/workitem.py` ≥ 85%
- [ ] `ruff check .`, `mypy src/` exit 0
- [ ] `bash scripts/audit.sh` exit 0
- [ ] HR-4 respeitada (frozen+strict+extra=forbid)
- [ ] Conventional Commit `(SPEC-009)`
