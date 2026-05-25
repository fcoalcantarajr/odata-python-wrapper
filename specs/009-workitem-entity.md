<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# SPEC-009: WorkItem entity — Pydantic frozen+strict model

- id: SPEC-009
- slug: workitem-entity
- status: IMPLEMENTED
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
Then pydantic.ValidationError is raised with "Extra inputs are not permitted"
```

### AC-3: strict type enforcement

```
Given OData JSON row with WorkItemId="abc" (string instead of int)
When WorkItem.model_validate(row)
Then pydantic.ValidationError is raised
```

### AC-4: fetch by ID returns WorkItem

```
Given mock HTTP returns WorkItem JSON for id=42
When client.get_workitem(42)
Then returns WorkItem with WorkItemId=42
```

### AC-5: frozen=True impede mutation

```
Given WorkItem instance
When instance.Title = "new"
Then TypeError is raised (frozen)
```

## INVEST self-score

- **I**ndependent: 9/10 — Depende do ODataEntity base (SPEC-001) e pydantic, mas não de outras entities; autocontido em módulo único.
- **N**egotiable: 8/10 — Lista de campos e detalhes de validação são negociáveis; frozen+strict+extra=forbid é fixo (HR-4).
- **V**aluable: 10/10 — Sem entities tipadas, consumidores parseiam raw dicts; schema drift fica indetectável até runtime.
- **E**stimable: 9/10 — Modelo Pydantic ~40 linhas + um método no client; padrão bem conhecido.
- **S**mall: 8/10 — ~80 linhas no total (test + model + método client); cabe em uma sessão.
- **T**estable: 10/10 — Todos os ACs testáveis com aioresponses + validação pydantic direta.

Média: 9.0/10

## Out-of-scope

- Outros entity sets (WorkItemRevisions, WorkItemSnapshot, etc.) — ficam para specs futuras.
- `$expand=Revisions` ou navegação — bloqueado pelo ADO (gotcha 5 / HR-14).
- Bulk CRUD / mutation — ADO Analytics é read-only.
- v2.0 compatibility (HR-19 fixa v4.0-preview).
- `WorkItemType` como Pydantic enum — mantido como `Literal` string por simplicidade.

## NFRs

- **Performance**: Model instantiation < 1ms per row em ambiente mock; sem blocking I/O.
- **Security**: Dados de validação não expõem PAT; sem logging de campos do modelo.
- **Observability**: ValidationError é propagada com mensagem clara; `__repr__` do modelo omite dados sensíveis.
- **Maintainability**: Novo modelo = novo arquivo em `entities/` + re-export em `__init__.py`.

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
