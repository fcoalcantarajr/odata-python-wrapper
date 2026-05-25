<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# SPEC-007: Serialization order — canonical query option ordering

- id: SPEC-007
- slug: serialization-order
- status: IMPLEMENTED
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
Then the serialized query string matches the regex `\$apply=.*&\$filter=.*&\$top=.*`
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

## NFRs

- **Performance:** Serialização de 7 query options completa em < 1ms (função pura sem IO, sem alocações pesadas).
- **Security:** N/A — serialização é puramente string; nenhum dado sensível é logado nem transita aqui.
- **Observability:** Log DEBUG pode emitir o dicionário de entrada e a query string serializada (sem expor secrets).

## INVEST self-score

- **I**ndependent: 10/10 — spec autocontido; depende apenas do módulo `query/_serialize.py` que ainda não existe.
- **N**egotiable:  9/10 — ordem canônica é fixa (HR-9), mas tratamento de unknown options poderia ser diferente.
- **V**aluable:    10/10 — sem isso toda request com >1 opção quebra com HTTP 400.
- **E**stimable:   9/10 — escopo claro, ~1h de implementação.
- **S**mall:       9/10 — módulo único, sem dependências externas.
- **T**estable:    10/10 — função pura, 5 ACs com assert de string.

Média: 9.5/10

## Out-of-scope

- Validação semântica dos valores das query options (ex: se `$top` é número válido).
- Formatação de valores de filtro (datas, aspas simples) — coberto em specs de filter/apply.
- Serialização de `$batch` requests — coberto em spec de batch.

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
