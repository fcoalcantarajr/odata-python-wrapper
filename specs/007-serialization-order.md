<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# SPEC-007: Serialization order — canonical query option ordering

- id: SPEC-007
- slug: serialization-order
- status: DRAFT
- created: 2026-05-22
- owner: @opencode

## User Story

As a developer using the ADO Analytics OData client, I want all query options serialized in the canonical order `$apply → $filter → $orderby → $expand → $select → $skip → $top` (HR-9), so that requests never get rejected with HTTP 400 due to option ordering.

## Use Cases

- UC1: Serialize dict of query options in canonical order.
- UC2: Ignore None/empty values.
- UC3: Missing options are simply omitted.
- UC4: Non-canonical options are appended at the end.

## Acceptance Criteria (Gherkin absoluto)

### AC-1: canonical order is respected

```
Given query = {"$filter": "x eq 1", "$top": "10", "$apply": "groupby((y))"}
When serialize(query)
Then URL query string contém "$apply" antes de "$filter" antes de "$top"
```

### AC-2: full order

```
Given query with all 7 options
When serialize(query)
Then order is $apply → $filter → $orderby → $expand → $select → $skip → $top
```

### AC-3: None/empty values omitted

```
Given query = {"$filter": "x eq 1", "$top": None, "$skip": ""}
When serialize(query)
Then only "$filter=x+eq+1" appears
```

### AC-4: unknown options appended at end

```
Given query = {"$filter": "x eq 1", "$custom": "val"}
When serialize(query)
Then "$custom=val" appears after all canonical options
```

### AC-5: empty dict returns empty string

```
Given query = {}
When serialize(query)
Then result is ""
```

## INVEST self-score

Média: 9.5/10

## Test plan

- AC-1 → `test_serialize.py::test_ac1_canonical_order_respected`
- AC-2 → `test_serialize.py::test_ac2_full_order`
- AC-3 → `test_serialize.py::test_ac3_none_empty_omitted`
- AC-4 → `test_serialize.py::test_ac4_unknown_options_appended`
- AC-5 → `test_serialize.py::test_ac5_empty_dict`

## DoD

- [ ] Todos AC verdes
- [ ] Coverage de `query/_serialize.py` ≥ 85%
- [ ] `ruff check .`, `mypy src/` exit 0
- [ ] `bash scripts/audit.sh` exit 0
- [ ] HR-9 respeitada
- [ ] Conventional Commit `(SPEC-007)`
