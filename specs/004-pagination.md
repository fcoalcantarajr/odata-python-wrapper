<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# SPEC-004: Pagination via AsyncIterator ($skip / $top + @odata.nextLink)

- id: SPEC-004
- slug: pagination
- status: IMPLEMENTED
- created: 2026-05-22
- owner: @opencode

## User Story

As a consumer do ADO Analytics OData, I want paginar resultados de qualquer entity set via um **AsyncIterator** que usa `$skip`/`$top` por padrão e respeita `@odata.nextLink` quando o servidor devolve um, so that eu posso processar datasets grandes sem carregar tudo em memória.

## Use Cases

- UC1: Iterar páginas via `$skip` com page size configurável (default 100 via `$top`).
- UC2: Se `@odata.nextLink` estiver presente, seguir a URL do nextLink.
- UC3: Parar quando página vazia OU sem nextLink.
- UC4: Configurar page size via parâmetro `top` (<1 rejeitado).
- UC5: Retentar busca individual com tenacity (SPEC-003) em TransientError.

## Acceptance Criteria (Gherkin absoluto)

### AC-1: $skip avança a cada iteração

```
Given um mock HTTP que retorna 10 itens por página (total 25 itens)
  And paginator = client.paginate("WorkItems", top=10)
When itero 3 páginas via `async for page in paginator`
Then a 1ª requisição contém `$top=10` e NÃO contém `$skip`
  And a 2ª requisição contém `$skip=10`
  And a 3ª requisição contém `$skip=20`
  And o somatório de itens das 3 páginas é 25
  And a iteração para sem fazer 4ª requisição
```

### AC-2: @odata.nextLink é seguido quando presente

```
Given um mock cujo 1º response contém `@odata.nextLink: "https://...?$skiptoken=abc"`
  And o 2º NÃO contém nextLink e retorna 5 itens
When itero via `async for page in paginator`
Then a 2ª requisição é exatamente a URL do nextLink (não `$skip`)
  And `len(pages) == 2`
```

### AC-3: Página vazia encerra iteração

```
Given um mock que retorna 10 itens na 1ª página (sem @odata.nextLink), 0 na 2ª
When itero via `async for page in paginator`
Then apenas 1 requisição HTTP foi feita
  And o loop yieldou 1 página
```

### AC-4: top < 1 levanta ValueError

```
Given paginator = client.paginate("WorkItems", top=0)
When a chamada é feita
Then é levantado `ValueError` com mensagem contendo "top must be >= 1"
```

### AC-5: AsyncIterator respeita o protocolo

```
Given paginator = client.paginate("WorkItems", top=100)
When chamo `await paginator.__anext__()` após o término
Then é levantado `StopAsyncIteration`
```

## NFRs

- **Performance:** Overhead < 1µs por página. $skip vs nextLink decidido em O(1).
- **Security:** nextLink URLs nunca logadas em INFO. DEBUG trunca a 200 chars.
- **Observability:** DEBUG log emite `paginate.start` e `paginate.page`.

## INVEST self-score

- **I**ndependent: 7/10 — Depende do HTTP layer (SPEC-002) mas não de features de alto nível
- **N**egotiable: 8/10 — Estratégia $skip vs nextLink poderia usar só nextLink
- **V**aluable: 10/10 — Sem paginação, datasets grandes causariam OOM ou timeout
- **E**stimable: 8/10 — AsyncIterator + $skip é implementação direta com AsyncGenerator
- **S**mall: 8/10 — Feature isolada em `_pagination.py`, ~100 linhas
- **T**estable: 10/10 — 5 ACs todos com mock HTTP + assertion numérica

Média: 8.5/10

## Out-of-scope

- POST $batch (SPEC-008), cache, $count, Pydantic parsing (SPEC-009), paralelismo

## Test plan

- AC-1 → `test_pagination.py::test_ac1_skip_advances`
- AC-2 → `test_pagination.py::test_ac2_nextlink_followed`
- AC-3 → `test_pagination.py::test_ac3_empty_page_stops`
- AC-4 → `test_pagination.py::test_ac4_invalid_top_raises_valueerror`
- AC-5 → `test_pagination.py::test_ac5_async_iterator_protocol`

## DoD

- [ ] Todos AC verdes
- [ ] Coverage de `_pagination.py` ≥ 85%
- [ ] `ruff check .`, `mypy src/` exit 0
- [ ] `bash scripts/audit.sh` exit 0
- [ ] Conventional Commit `(SPEC-004)`
