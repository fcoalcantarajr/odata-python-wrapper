<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# SPEC-011: Fluent API — query builder on top of DSLs

- id: SPEC-011
- slug: fluent-api
- status: DRAFT
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
Then contains "$filter" then "$select" then "$top" in canonical order
```

### AC-3: get() executes and parses

```
Given builder.filter(...).get()
When called
Then returns list[dict] from HTTP response
```

### AC-4: paginate() returns async iterator

```
Given builder.filter(...).paginate(top=100)
When used in async for
Then yields pages
```

### AC-5: chaining preserves immutability

```
Given b1 = query.filter(...)
  And b2 = b1.top(10)
When compared
Then str(b1) != str(b2)
```

## INVEST self-score

Média: 8.5/10

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
