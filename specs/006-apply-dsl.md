<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# SPEC-006: $apply DSL — fluent builder for OData aggregations

- id: SPEC-006
- slug: apply-dsl
- status: DRAFT
- created: 2026-05-22
- owner: @opencode

## User Story

As a developer querying Azure DevOps Analytics WorkItemSnapshot entities (which require $apply), I want a fluent builder that constructs `$apply` expressions from method calls — groupby(), filter(), aggregate() — so that I can compose aggregation queries without manual string concatenation.

## Use Cases

- UC1: `Apply.groupby("Field")` → `$apply=groupby((Field))`
- UC2: `Apply.filter(filter_obj)` → `$apply=filter(…)`
- UC3: `Apply.aggregate("Field", "sum")` → `$apply=aggregate(Field with sum)`
- UC4: `Apply.groupby(["F1","F2"]).aggregate("F3","sum")` → composto
- UC5: WorkItemSnapshot enforcement — ValueError se sem groupby(DateSK) (HR-13)
- UC6: Múltiplas aggregations no mesmo groupby

## Acceptance Criteria (Gherkin absoluto)

### AC-1: single groupby

```
Given Apply builder vazio
When `.groupby("State")`
Then `str(apply) == "$apply=groupby((State))"`
```

### AC-2: groupby multi-campo

```
Given Apply builder vazio
When `.groupby(["State","Priority"])`
Then `str(apply) == "$apply=groupby((State,Priority))"`
```

### AC-3: filter wrapping

```
Given Apply vazio + FilterExpr representando `State eq 'Active'`
When `.filter(filter_expr)`
Then `str(apply) == "$apply=filter(State eq 'Active')"`
```

### AC-4: aggregate

```
Given Apply builder vazio
When `.aggregate("Effort", "sum")`
Then `str(apply) == "$apply=aggregate(Effort with sum)"`
```

### AC-5: composto groupby + aggregate

```
Given Apply vazio
When `.groupby(["TeamProject","WorkItemType"]).aggregate("Count","sum")`
Then `str(apply) == "$apply=groupby((TeamProject,WorkItemType))/aggregate(Count with sum)"`
```

### AC-6: múltiplas agregações

```
Given Apply vazio
When `.groupby("State").aggregate("Count","sum").aggregate("Effort","avg")`
Then result contains "aggregate(Count with sum, Effort with avg)"
```

### AC-7: enforce HR-13 — Snapshot sem groupby levanta erro

```
Given Apply com entity_type="WorkItemSnapshot", sem groupby(DateSK/DateValue)
When `.validate()`
Then `ValueError` com "WorkItemSnapshot" e "groupby(DateSK)"
```

### AC-8: enforce HR-13 — Snapshot COM groupby passa

```
Given Apply com entity_type="WorkItemBoardSnapshot", groupby("DateValue")
When `.validate()`
Then retorna None
```

## NFRs

- **Performance:** Serialização O(n) para até 20 cláusulas, < 1ms.
- **Security:** $apply nunca expõe PAT.
- **Observability:** DEBUG log mostra $apply serializado.

## INVEST self-score

- **I**ndependent: 9/10 — Não depende de outras specs; define o builder `Apply` isoladamente (apenas referência FilterExpr de SPEC-005 como input).
- **N**egotiable: 8/10 — Nomes de método e ordem de composição são negociáveis, mas a estrutura `groupby → filter → aggregate` é fixa por definição OData.
- **V**aluable: 9/10 — Developer pode compor `$apply` sem string concat manual; valor direto pro caso de uso WorkItemSnapshot.
- **E**stimable: 9/10 — 4 métodos públicos (groupby, filter, aggregate, validate), escopo claro, < 1 dia de impl.
- **S**mall: 8/10 — Cabe em uma sessão, mas o `_serialize.py` (SPEC-007) pode forçar pequeno refactor depois.
- **T**estable: 10/10 — Todos os 8 AC têm Then com igualdade de string, exceção nomeada ou substring; 100% testável em unidade.

Média: 8.8/10

## Out-of-scope

- FilterExpr builder (SPEC-005), serialization order (SPEC-007), $batch (SPEC-008), Pydantic (SPEC-009), fluent API (SPEC-011)

## Test plan

- AC-1 → `test_apply_dsl.py::test_ac1_groupby_single_field`
- AC-2 → `test_apply_dsl.py::test_ac2_groupby_multiple_fields`
- AC-3 → `test_apply_dsl.py::test_ac3_filter_wrapping`
- AC-4 → `test_apply_dsl.py::test_ac4_aggregate_method`
- AC-5 → `test_apply_dsl.py::test_ac5_groupby_then_aggregate`
- AC-6 → `test_apply_dsl.py::test_ac6_multiple_aggregations`
- AC-7 → `test_apply_dsl.py::test_ac7_enforce_snapshot_requires_groupby`
- AC-8 → `test_apply_dsl.py::test_ac8_enforce_snapshot_with_valid_groupby`

## DoD

- [ ] Todos AC verdes
- [ ] Coverage do módulo `query/apply.py` ≥ 85%
- [ ] `ruff check .`, `mypy src/` exit 0
- [ ] `bash scripts/audit.sh` exit 0
- [ ] HARD RULES: HR-4, HR-9, HR-13
- [ ] Conventional Commit `(SPEC-006)`
