<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# SPEC-003: Retry com tenacity — TransientError/RateLimitError com exponential backoff + jitter

- id: SPEC-003
- slug: retry-tenacity
- status: IMPLEMENTED
- created: 2026-05-22
- owner: @opencode

## User Story

As a desenvolvedor integrando com Azure DevOps Analytics OData, I want chamadas HTTP que falham por causa transitória (5xx, connection reset, rate limit 429) serem retentadas automaticamente com exponential backoff + jitter via `tenacity`, e que erros definitivos (401, 203+text/html, 400) **nunca** sejam retentados, so that o client é resiliente a picos de carga e falhas de rede sem mascarar erros de configuração ou autenticação.

## Use Cases

- UC1: **TransientError** (5xx, connection reset, timeout) → retry com exponential backoff + jitter, até `max_attempts` tentativas.
- UC2: **RateLimitError** (429) → retry respeitando `Retry-After` header, limitado a 3 tentativas independente do `max_attempts` geral.
- UC3: **AuthenticationError** (401, 203+text/html) → **NEVER retry** (HR-15); exceção propagada imediatamente.
- UC4: **BadRequestError** (400) → **NEVER retry**; exceção propagada imediatamente.
- UC5: **Max retries excedido** → a última exceção original (não wrapper) é propagada para o caller.
- UC6: **Configuração** — `with_retry` aceita `max_attempts`, `min_delay`, `max_delay` como parâmetros opcionais com defaults seguros.

## Acceptance Criteria (Gherkin absoluto)

### AC-1: TransientError aciona retry com backoff + jitter

```
Given um mock HTTP que retorna 503 (Service Unavailable) nas primeiras 2 chamadas e 200 na 3ª
When invoco uma função decorada com `@with_retry`
Then a função retorna o resultado bem-sucedido da 3ª chamada (não propaga exceção)
  And a função mockada foi chamada exatamente 3 vezes
```

### AC-2: RateLimitError respeita Retry-After e tem cap de 3 tentativas

```
Given um mock HTTP que retorna 429 com header `Retry-After: 2` por 4 chamadas consecutivas
When invoco uma função decorada com `@with_retry(max_attempts=5)`
Then a exceção propagada é `RateLimitError`
  And a função mockada foi chamada exatamente 3 vezes (cap de rate-limit, não 5)
```

### AC-3: AuthenticationError NUNCA é retentado (HR-15)

```
Given um mock HTTP que retorna 401 na primeira chamada
When invoco uma função decorada com `@with_retry`
Then a exceção propagada é `AuthenticationError`
  And a função mockada foi chamada exatamente 1 vez (zero retries)
```

### AC-4: BadRequestError NUNCA é retentado

```
Given um mock HTTP que retorna 400 na primeira chamada
When invoco uma função decorada com `@with_retry`
Then a exceção propagada é `BadRequestError`
  And a função mockada foi chamada exatamente 1 vez (zero retries)
```

### AC-5: Max retries excedido propaga a última exceção original

```
Given um mock HTTP que retorna 503 em todas as chamadas
  And `max_attempts=3` configurado
When invoco uma função decorada com `@with_retry(max_attempts=3)`
Then a exceção propagada é `TransientError` (a mesma instância da 3ª tentativa, não um wrapper)
  And a função mockada foi chamada exatamente 3 vezes
```

### AC-6: Parâmetros configuráveis são respeitados

```
Given um mock HTTP que retorna 503 nas 4 primeiras chamadas e 200 na 5ª
  And `max_attempts=5` configurado
When invoco `with_retry(fn, max_attempts=5, min_delay=0.01, max_delay=0.05)`
Then a função retorna o resultado bem-sucedido
  And a função mockada foi chamada exatamente 5 vezes
  And o tempo total decorrido é < 1 segundo
```

### AC-7: Decorator preserva async signature e type hints

```
Given uma função `async def fetch_data(arg: int) -> str` decorada com `@with_retry`
When inspeciono `inspect.signature(fetch_data)`
Then os parâmetros na assinatura incluem `arg` com type hint `int`
  And o return type hint é `str`
```

## NFRs

- **Performance:** p50 delay adicional < 10ms em caso sem retry. Backoff respeita `min_delay`/`max_delay` configurados.
- **Security:** PAT mascarado em logs de retry (apenas `pat[:6] + "..."`). Nenhuma exceção serializada vaza o PAT completo (HR-16).
- **Observability:** Cada tentativa de retry loga em `WARNING` o attempt number, exceção, e delay calculado.

## INVEST self-score

- **I**ndependent: 8/10 — depende da hierarquia de exceções de SPEC-002
- **N**egotiable:  9/10 — detalhes de jitter e valores default são negociáveis; HR-15 é fixo
- **V**aluable:    10/10 — sem retry o client é frágil
- **E**stimable:   9/10 — tenacity é biblioteca madura
- **S**mall:       9/10 — ~50 linhas de impl em `retry.py`
- **T**estable:    10/10 — 7 AC todos observáveis

Média: 9.2/10

## Out-of-scope

- POST $batch retry (SPEC-008)
- Circuit breaker
- Retry em streaming/paginação (SPEC-004)

## Test plan

- AC-1 → `tests/unit/test_retry_tenacity.py::test_ac1_transient_retry_success_after_retries`
- AC-2 → `tests/unit/test_retry_tenacity.py::test_ac2_ratelimit_capped_at_three`
- AC-3 → `tests/unit/test_retry_tenacity.py::test_ac3_auth_error_never_retried`
- AC-4 → `tests/unit/test_retry_tenacity.py::test_ac4_bad_request_never_retried`
- AC-5 → `tests/unit/test_retry_tenacity.py::test_ac5_max_attempts_propagates_last_exception`
- AC-6 → `tests/unit/test_retry_tenacity.py::test_ac6_configurable_params_respected`
- AC-7 → `tests/unit/test_retry_tenacity.py::test_ac7_decorator_preserves_signature`

## DoD

- [ ] Todos AC verdes em `uv run pytest -q tests/unit/test_retry_tenacity.py`
- [ ] Coverage de `retry.py` ≥ 85%
- [ ] `ruff check .`, `mypy src/` exit 0
- [ ] `bash scripts/audit.sh` exit 0
- [ ] HARD RULES: HR-15, HR-16
- [ ] Conventional Commit referenciando `(SPEC-003)`
