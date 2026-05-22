<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# SPEC-008: POST $batch — URL > 3000 chars switch to multipart/mixed

- id: SPEC-008
- slug: batch-post
- status: DRAFT
- created: 2026-05-22
- owner: @opencode

## User Story

As a developer querying ADO Analytics, I want URLs exceeding 3000 characters to automatically switch to `POST $batch` multipart/mixed (HR-10), so that long queries with many $filter conditions don't get rejected by URL length limits.

## Use Cases

- UC1: URL ≤ 3000 chars → normal GET request.
- UC2: URL > 3000 chars → POST $batch with multipart/mixed content.
- UC3: $batch response parsed back as if it were a direct response.
- UC4: Configurable threshold (default 3000).

## Acceptance Criteria (Gherkin absoluto)

### AC-1: URL ≤ 3000 chars → GET

```
Given uma query que resulta em URL de 2500 chars
When client.get("WorkItems") é chamado
Then o método HTTP usado é GET (não POST)
```

### AC-2: URL > 3000 chars → POST $batch

```
Given uma query que resulta em URL de 3500 chars
When client.get("WorkItems") é chamado
Then o método HTTP usado é POST
  And o path da requisição termina em "/$batch"
  And o Content-Type contém "multipart/mixed"
```

### AC-3: $batch response parsed corretamente

```
Given um response $batch com boundary e parte única contendo JSON
When client.get("WorkItems") com URL > 3000 chars
Then o dict retornado contém os mesmos dados que viriam do GET direto
```

### AC-4: threshold configurável

```
Given client.get("WorkItems") com URL de 2000 chars e threshold=1000
When chamado
Then método HTTP é POST $batch (threshold menor que URL)
```

## INVEST self-score

Média: 8.8/10

## Test plan

- AC-1 → `test_batch.py::test_ac1_short_url_uses_get`
- AC-2 → `test_batch.py::test_ac2_long_url_uses_post_batch`
- AC-3 → `test_batch.py::test_ac3_batch_response_parsed`
- AC-4 → `test_batch.py::test_ac4_configurable_threshold`

## DoD

- [ ] Todos AC verdes
- [ ] Coverage do módulo `_batch.py` ≥ 85%
- [ ] `ruff check .`, `mypy src/` exit 0
- [ ] `bash scripts/audit.sh` exit 0
- [ ] HR-10 respeitada
- [ ] Conventional Commit `(SPEC-008)`
