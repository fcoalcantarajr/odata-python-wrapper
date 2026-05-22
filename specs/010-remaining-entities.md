<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# SPEC-010: Remaining entities — 11 entity models

- id: SPEC-010
- slug: remaining-entities
- status: DRAFT
- created: 2026-05-22
- owner: @opencode

## User Story

As a developer using ADO Analytics OData, I want Pydantic models for all remaining entity sets (WorkItemRevisions, Iteration, Project, Team, WorkItemBoardSnapshot, etc.) so that all API responses are type-checked and schema-drift-detected.

## Use Cases

- UC1: WorkItemRevisions model (HR-14: no $expand=Revisions, use entity set).
- UC2: WorkItemBoardSnapshot / WorkItemBoardSnapshotWithDescription models.
- UC3: Iteration / Project / Team / Area models.
- UC4: Remaining system entity sets.
- UC5: All models inherit ODataEntity (frozen+strict+extra=forbid, HR-4).

## Acceptance Criteria (Gherkin absoluto)

### AC-1: WorkItemRevisions model

```
Given OData JSON row for WorkItemRevisions
When WorkItemRevisions.model_validate(row)
Then instance.Revision is int >= 1
  And instance.WorkItemId is int
```

### AC-2: WorkItemBoardSnapshot model

```
Given OData JSON row for WorkItemBoardSnapshot
When WorkItemBoardSnapshot.model_validate(row)
Then instance.DateSK is int (YYYYMMDD)
```

### AC-3: Iteration model

```
Given OData JSON row for Iteration
When Iteration.model_validate(row)
Then instance.Identifier is str (not None)
```

### AC-4: Project model

```
Given OData JSON row for Project
When Project.model_validate(row)
Then instance.ProjectSK is int
  And instance.ProjectName is str
```

### AC-5: Team model

```
Given OData JSON row for Team
When Team.model_validate(row)
Then instance.TeamSK is int
  And instance.TeamName is str
```

### AC-6: All models are frozen+strict

```
Given any entity model class
When inspected
Then model_config.frozen == True
  And model_config.strict == True
  And model_config.extra == "forbid"
```

## INVEST self-score

Média: 8.3/10

## Test plan

- AC-1 → `test_remaining_entities.py::test_ac1_work_item_revisions`
- AC-2 → `test_remaining_entities.py::test_ac2_board_snapshot`
- AC-3 → `test_remaining_entities.py::test_ac3_iteration`
- AC-4 → `test_remaining_entities.py::test_ac4_project`
- AC-5 → `test_remaining_entities.py::test_ac5_team`
- AC-6 → `test_remaining_entities.py::test_ac6_all_frozen_strict`

## DoD

- [ ] Todos AC verdes
- [ ] Coverage de `entities/` ≥ 85%
- [ ] `ruff check .`, `mypy src/` exit 0
- [ ] `bash scripts/audit.sh` exit 0
- [ ] HR-4, HR-13, HR-14 respeitadas
- [ ] Conventional Commit `(SPEC-010)`
