<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# SPEC-011: Fluent API — query builder on top of DSLs

- id: SPEC-011
- slug: fluent-api
- status: IMPLEMENTED
- created: 2026-05-22
- owner: @opencode

## User Story

As a developer writing queries, I want a fluent builder `client.query("WorkItems").filter(...).select(["Title","State"]).apply(...).top(100)` that composes all DSLs (SPEC-005/006/007) into a single chain, so that complex queries are readable and type-safe.

## Use Cases

- UC1: `client.query("WorkItems")` returns a QueryBuilder.
- UC2: `.filter(filter_expr)` delegates to $filter builder (SPEC-005).
- UC3: `.apply(apply_obj)` delegates to $apply builder (SPEC-006).
- UC4: `.select(["Field1","Field2"])` → `$select=Field1,Field2`.
- UC5: `.orderby("Field", asc/desc)` → `$orderby=Field asc`.
- UC6: `.top(n)` / `.skip(n)` → `$top=n` / `$skip=n`.
- UC7: `.expand("Field")` → `$expand=Field`.
- UC8: `.get()` executes and returns parsed entities.
- UC9: `.paginate()` returns AsyncIterator (SPEC-004).

## Acceptance Criteria (Gherkin absoluto)

### AC-1: query builder starts empty

```
Given client.query("WorkItems")
When str(builder)
Then ""
```

### AC-2: filter+select+top serializes correctly

```
Given builder.filter(Filter.eq("State","Active")).select(["Title","State"]).top(10)
When str(builder)
Then "$filter=State eq 'Active'&$select=Title,State&$top=10"
```

### AC-3: get() executes and parses

```
Given aioresponses mock GET ".../WorkItems?$filter=State eq 'Active'" returning {"value":[{"Id":1,"Title":"Bug A"}]}
When await builder.filter(Filter.eq("State","Active")).get()
Then dict with {"value":[{"Id":1,"Title":"Bug A"}]}
```

### AC-4: paginate() returns async iterator

```
Given aioresponses mock 2 pages: page1 with 2 items + @odata.nextLink, page2 with 1 item
When async for page in builder.paginate(top=2)
Then len(pages) == 2, first page has 2 items, second page has 1 item
```

### AC-5: chaining preserves immutability

```
Given b1 = query.filter(...)
  And b2 = b1.top(10)
When str(b1) and str(b2)
Then str(b1) == "" and str(b2) == "$top=10"
```

## NFRs

- **Performance**: `str(builder)` deve ser O(n) no número de cláusulas, sem I/O.
- **Security**: Builder não armazena PAT; execução delega ao `client._session`.
- **Observability**: `repr(builder)` expõe entity set e cláusulas ativas.

## Out-of-scope

- Type hints genéricos por entity set (`QueryBuilder[WorkItem]`).
- Validação semântica de campos (ex: verificar se `State` existe no ADO).
- Mutação in-place (sempre retorna nova instância).
- Suporte a `$search` (não coberto pelos DSLs base).

## INVEST self-score

- **I**ndependent: 7/10 — Depende de SPEC-004/005/006/007.
- **N**egotiable: 8/10 — Nomes dos métodos podem mudar.
- **V**aluable: 9/10 — Composição type-safe de queries complexas.
- **E**stimable: 8/10 — Wrapper sobre DSLs existentes.
- **S**mall: 8/10 — Wrapper sobre DSLs existentes; padrão repetitivo.
- **T**estable: 8/10 — ACs com strings exatas e assertions de igualdade.

Média: 8.0/10

## Test plan

- AC-1 → `test_fluent_api.py::test_ac1_empty_builder`
- AC-2 → `test_fluent_api.py::test_ac2_serialization`
- AC-3 → `test_fluent_api.py::test_ac3_get_executes`
- AC-4 → `test_fluent_api.py::test_ac4_paginate`
- AC-5 → `test_fluent_api.py::test_ac5_immutability`

## DoD

- [ ] Todos AC verdes
- [ ] Coverage de `query/builder.py` ≥ 85%
- [ ] `ruff check .`, `mypy src/` exit 0
- [ ] `bash scripts/audit.sh` exit 0
- [ ] Conventional Commit `(SPEC-011)`
