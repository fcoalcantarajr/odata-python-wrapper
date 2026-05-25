<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# SPEC-008: POST $batch — URL > 3000 chars switch to multipart/mixed

- id: SPEC-008
- slug: batch-post
- status: IMPLEMENTED
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
Given um response $batch com boundary e parte única contendo JSON com uma resposta HTTP 200
When client.get("WorkItems") com URL > 3000 chars
Then o dict retornado por client.get() é semanticamente igual (`==`) ao dict que seria retornado por um GET direto para a mesma URL
  And contém as chaves `@odata.context`, `value`, e opcionalmente `@odata.nextLink`
```

### AC-4: threshold configurável

```
Given client.get("WorkItems") com URL de 2000 chars e threshold=1000
When client.get("WorkItems") é chamado
Then método HTTP é POST $batch (threshold menor que URL)
```

### AC-5: URL exatamente igual ao threshold → GET

```
Given uma query que resulta em URL de 3000 chars com threshold default (3000)
When client.get("WorkItems") é chamado
Then o método HTTP usado é GET (não POST)
```

```
Given uma query que resulta em URL de 3000 chars com threshold default (3000)
When client.get("WorkItems") é chamado
Then o método HTTP usado é GET (não POST)
```

## Out-of-scope

- Múltiplas requests em um único $batch — apenas wrapping de 1 GET.
- Upload/POST dentro de $batch.
- Erro HTTP dentro da parte batch (e.g., 404/400 no inner request) — o client retorna o erro da parte como se fosse do GET direto; sem lógica extra.
- v2.0 compatibility (HR-19 fixa v4.0-preview).

## NFRs

- **Performance**: Overhead do parsing multipart < 50ms em ambiente mock; sem blocking I/O na extração (tudo `await`).
- **Security**: PAT mascarado em logs mesmo no body $batch; querystring completa não logada em nível INFO.
- **Observability**: Log DEBUG exibe boundary UUID, payload size antes do switch, status code do inner request no response.
- **Reliability**: Se o $batch response não for multipart/mixed (e.g., erro 203 non-auth), o error mapping de SPEC-002 (parse_response) deve ser respeitado.

## INVEST self-score

- **I**ndependent: 8/10 — Depende de SPEC-001 (session/URL builder) mas não de specs posteriores; a lógica $batch é autocontida em módulo único.
- **N**egotiable: 8/10 — Nome do módulo, default do threshold, e formato exato do multipart boundary são negociáveis; o switch automático é fixo.
- **V**aluable: 10/10 — Sem HR-10, queries longas geram HTTP 400 (URL muito grande); blocker pra cenários com filtros complexos e muitos campos.
- **E**stimable: 9/10 — Padrão $batch multipart está documentado no skill do projeto; parsing de multipart é bem conhecido.
- **S**mall: 8/10 — ~80 linhas em módulo novo `_batch.py` + modificação pontual no serializer/client; cabe em uma sessão.
- **T**estable: 9/10 — AC-1/AC-2/AC-4 são diretos com aioresponses; AC-3 requer fixture de response multipart mas é factível com raw bytes.

Média: 8.7/10

## Test plan

- AC-1 → `test_batch.py::test_ac1_short_url_uses_get`
- AC-2 → `test_batch.py::test_ac2_long_url_uses_post_batch`
- AC-3 → `test_batch.py::test_ac3_batch_response_parsed`
- AC-4 → `test_batch.py::test_ac4_configurable_threshold`
- AC-5 → `test_batch.py::test_ac5_exact_threshold_uses_get`

## DoD

- [ ] Todos AC verdes
- [ ] Coverage do módulo `_batch.py` ≥ 85%
- [ ] `ruff check .`, `mypy src/` exit 0
- [ ] `bash scripts/audit.sh` exit 0
- [ ] HR-10 respeitada
- [ ] Conventional Commit `(SPEC-008)`
