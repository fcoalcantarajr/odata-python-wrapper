<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# SPEC-010: Remaining entities — 11 entity models

- id: SPEC-010
- slug: remaining-entities
- status: IMPLEMENTED
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

### AC-7: WorkItemBoardSnapshotWithDescription includes Description

```
Given OData JSON row with Description field
When WorkItemBoardSnapshotWithDescription.model_validate(row)
Then instance.Description is str
```

### AC-8: Area model

```
Given OData JSON row for Area
When Area.model_validate(row)
Then instance.AreaSK is int
  And instance.AreaPath is str
```

### AC-9: Date model

```
Given OData JSON row for Date dimension
When Date.model_validate(row)
Then instance.DateSK is int (YYYYMMDD)
  And instance.Year is int
```

### AC-10: User model

```
Given OData JSON row for User
When User.model_validate(row)
Then instance.UserSK is int
  And instance.UserName is str
```

### AC-11: WorkItemType model

```
Given OData JSON row for WorkItemType
When WorkItemType.model_validate(row)
Then instance.WorkItemTypeSK is int
  And instance.WorkItemTypeName is str
```

### AC-12: WorkItemLink model

```
Given OData JSON row for WorkItemLink
When WorkItemLink.model_validate(row)
Then instance.SourceWorkItemId is int
  And instance.LinkType is str
```

## NFRs

- **Performance:** Model validation ≤ 100µs per instance (benchmark opcional no test).
- **Security:** N/A — models são data classes sem lógica de auth.
- **Observability:** N/A — models não emitem log diretamente.

## Out-of-scope

- Entidades além dos 11 modelos listados (Build, Release, Test).
- Navigation properties (`$expand`) entre entidades.
- Entity sets da área "Build" ou "Release" do ADO Analytics OData.
- Client methods que retornam typed entities (ex: `client.get_iteration(id_)`) — implementação via QueryBuilder (SPEC-011).
- Validação de `$apply groupby` para BoardSnapshot (enforced no Apply DSL, HR-13).

## INVEST self-score

| Letra | Score | Justificativa |
|-------|-------|--------------|
| **I**ndependent | 8 | Depende de ODataEntity (SPEC-009), aditivo |
| **N**egotiable | 8 | Field lists são negociáveis; 11 modelos são explícitos e acordados |
| **V**aluable | 9 | Type safety e schema-drift-detection |
| **E**stimable | 7 | 11 modelos nomeados com fields; escopo claro |
| **S**mall | 8 | 11 modelos seguem o mesmo padrão de WorkItem (~15 linhas cada), total ~315 linhas — cabe em uma sessão |
| **T**estable | 8 | ACs com type checking e valor assertions |
| **Média** | **8.0** | |

## Test plan

- AC-1 → `test_remaining_entities.py::test_ac1_work_item_revisions`
- AC-2 → `test_remaining_entities.py::test_ac2_board_snapshot`
- AC-3 → `test_remaining_entities.py::test_ac3_iteration`
- AC-4 → `test_remaining_entities.py::test_ac4_project`
- AC-5 → `test_remaining_entities.py::test_ac5_team`
- AC-6 → `test_remaining_entities.py::test_ac6_all_frozen_strict`
- AC-7 → `test_remaining_entities.py::test_ac7_board_snapshot_with_description`
- AC-8 → `test_remaining_entities.py::test_ac8_area`
- AC-9 → `test_remaining_entities.py::test_ac9_date`
- AC-10 → `test_remaining_entities.py::test_ac10_user`
- AC-11 → `test_remaining_entities.py::test_ac11_work_item_type`
- AC-12 → `test_remaining_entities.py::test_ac12_work_item_link`

## DoD

- [ ] Todos AC verdes
- [ ] Coverage de `entities/` ≥ 85%
- [ ] `ruff check .`, `mypy src/` exit 0
- [ ] `bash scripts/audit.sh` exit 0
- [ ] HR-4, HR-13, HR-14 respeitadas
- [ ] Conventional Commit `(SPEC-010)`
