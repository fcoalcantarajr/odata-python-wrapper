<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# SPEC-002: Mapeamento de erros de autenticação (401, 203+text/html → AuthenticationError) + PAT mascarado

- id: SPEC-002
- slug: auth-error-mapping
- status: DRAFT
- created: 2026-05-22
- owner: @opencode

## User Story

As a desenvolvedor usando o `AdoODataClient` para consultar o Azure DevOps Analytics OData, I want que respostas **401** e **203+text/html** levantem `AuthenticationError` (sem retry), respostas **400** levantem `BadRequestError`, respostas **5xx** levantem `TransientError`, respostas **429** levantem `RateLimitError`, e que o **PAT** seja **sempre** mascarado em logs, so that erros de autenticação nunca sejam confundidos com erros transitórios, o PAT nunca vaze em texto plano, e cada classe de erro seja tratável separadamente pelo retry/error-handling upstream.

## Use Cases

- **UC1:** HTTP 401 (Unauthorized) → `AuthenticationError` — não retentável, pois credenciais inválidas não se tornam válidas com tempo.
- **UC2:** HTTP 203 + `Content-Type: text/html` (sign-in page HTML) → `AuthenticationError` — PAT inválido ou expirado (HR-15 / gotcha 8). Também não retentável.
- **UC3:** PAT mascarado em **todas** as saídas de log (DEBUG do request/response, repr, str, exception messages) — nunca mais que 6 primeiros caracteres + `...` (HR-16).
- **UC4:** Erros não-autenticação (400 → `BadRequestError`, 404 → `AdoODataError` genérico, 5xx → `TransientError`, 429 → `RateLimitError`) passam para os tipos de exceção apropriados definidos em `exceptions.py`.

## Acceptance Criteria (Gherkin absoluto)

Cada AC tem Then **observável** (exceção nomeada, status code, igualdade de string, identidade de objeto).

### AC-1: 401 → AuthenticationError (não retentável)

```
Given uma instância de AdoODataClient dentro do async with
  And um mock HTTP que retorna status=401 com Content-Type: application/json
When client.get("WorkItems") é chamado
Then a exceção levantada é `AuthenticationError`
  And `AuthenticationError` é subclasse de `AdoODataError`
  And NÃO é subclasse de `TransientError`
```

### AC-2: 203 + Content-Type text/html → AuthenticationError com mensagem "203"

```
Given uma instância de AdoODataClient dentro do async with
  And um mock HTTP que retorna status=203 com Content-Type: text/html
  And corpo HTML contendo "Sign in to your account"
When client.get("WorkItems") é chamado
Then a exceção levantada é `AuthenticationError`
  And a mensagem da exceção contém a substring "203"
```

### AC-3: 400 → BadRequestError com mensagem do servidor

```
Given uma instância de AdoODataClient dentro do async with
  And um mock HTTP que retorna status=400 com Content-Type: application/json
  And corpo JSON {"error": {"message": "Invalid query option $select"}}
When client.get("WorkItems") é chamado
Then a exceção levantada é `BadRequestError`
  And a mensagem da exceção contém "Invalid query option"
  And `BadRequestError` NÃO é subclasse de `TransientError`
```

### AC-4: 502 → TransientError (retentável)

```
Given uma instância de AdoODataClient dentro do async with
  And um mock HTTP que retorna status=502 com Content-Type: application/json
When client.get("WorkItems") é chamado
Then a exceção levantada é `TransientError`
  And a mensagem da exceção contém "502"
```

### AC-5: 429 → RateLimitError (subclasse de TransientError)

```
Given uma instância de AdoODataClient dentro do async with
  And um mock HTTP que retorna status=429 com Content-Type: application/json
  And header Retry-After: 30
When client.get("WorkItems") é chamado
Then a exceção levantada é `RateLimitError`
  And `RateLimitError` é subclasse de `TransientError`
  And a mensagem da exceção contém "429"
```

### AC-6: PAT mascarado em DEBUG log na chamada get()

```
Given uma instância de AdoODataClient(pat="abcdef1234567890") dentro do async with
  And o logger `ado_odata_async._http` em nível DEBUG
  And um mock HTTP que retorna status=200
When client.get("WorkItems") é chamado
Then o log DEBUG emitido contém o PAT apenas como "abcdef..."
  And o log DEBUG NÃO contém a string "abcdef1234567890" (PAT completo)
```

### AC-7: 200 → parse_response retorna dict normalmente (sem exceção)

```
Given uma instância de AdoODataClient dentro do async with
  And um mock HTTP que retorna status=200 com Content-Type: application/json
  And corpo JSON {"value": [{"Id": 1}], "@odata.count": 1}
When client.get("WorkItems") é chamado
Then o retorno é um dict com chave "value" contendo lista
  And dict["@odata.count"] == 1 (igualdade numérica)
```

## NFRs

- **Performance:** A validação de status code e Content-Type é O(1) — sem impacto mensurável no hot path. parse_response adiciona < 1µs sobre o custo do JSON decode.
- **Security:** PAT nunca aparece completo em log, repr, str, ou exception message. `mask_pat()` aplicado em todas as saídas (HR-16). A função `build_basic_auth` garante username vazio (HR-8/gotcha 1).
- **Observability:** DEBUG log em `_http.py` exibe method, url, status code, e PAT mascarado. WARNING log para 4xx e 5xx com info suficiente pra debug sem expor o PAT.

## INVEST self-score

- **I**ndependent: 9/10 — depende de SPEC-001 (`client.py` com `get()` e `auth.py` stub), mas a lógica de `parse_response` e `build_basic_auth` é independente; testável com `aioresponses` sem o client real.
- **N**egotiable: 8/10 — o texto exato das mensagens de erro pode mudar; o mapeamento 404 → `AdoODataError` vs `BadRequestError` é negociável; o nível de log (INFO vs WARNING) é ajustável.
- **V**aluable: 10/10 — sem este spec, PAT vaza em logs (falha de segurança) e 203+HTML seria retried infinitamente (violação HR-15).
- **E**stimable: 9/10 — tabela de mapeamento HTTP→exceção é direta; `parse_response` são ~30 linhas; `build_basic_auth` é 1 linha.
- **S**mall: 8/10 — ~80 linhas de impl em `_http.py` + `auth.py` + ajuste em `client.py`; cabe em uma sessão.
- **T**estable: 10/10 — cada AC mocka um HTTP status diferente e asserctiona a exceção exata ou o conteúdo do log; `aioresponses` + `caplog` tornam cada teste deterministico.

Média: 9.0/10 (mínimo 8 para APPROVED)

## Out-of-scope

- Retry automático com tenacity (→ SPEC-003).
- Paginação de respostas (→ SPEC-004).
- Construção de query options (→ SPEC-005/006/007).
- POST $batch para URLs longas (→ SPEC-008).
- Timeout de conexão (→ SPEC-003, como gatilho de retry).
- Suporte a v2.0 (ADR-001 fixa v4.0-preview como única versão suportada; HR-19).

## Test plan

- AC-1 → `tests/unit/test_auth_error_mapping.py::test_ac1_401_raises_authentication_error`
- AC-2 → `tests/unit/test_auth_error_mapping.py::test_ac2_203_html_raises_authentication_error`
- AC-3 → `tests/unit/test_auth_error_mapping.py::test_ac3_400_raises_bad_request_error`
- AC-4 → `tests/unit/test_auth_error_mapping.py::test_ac4_502_raises_transient_error`
- AC-5 → `tests/unit/test_auth_error_mapping.py::test_ac5_429_raises_rate_limit_error`
- AC-6 → `tests/unit/test_auth_error_mapping.py::test_ac6_pat_masked_in_debug_log`
- AC-7 → `tests/unit/test_auth_error_mapping.py::test_ac7_200_returns_dict_parsed`

## DoD

- [ ] Todos AC verdes em `uv run pytest -q tests/unit/test_auth_error_mapping.py`
- [ ] Coverage de `_http.py` + `auth.py` ≥ 85%
- [ ] `ruff check .` exit 0
- [ ] `mypy src/` strict exit 0
- [ ] `bash scripts/audit.sh` exit 0
- [ ] HARD RULES respeitadas: HR-8 (empty user), HR-15 (203+html → AuthenticationError, sem retry), HR-16 (PAT mascarado)
- [ ] Conventional Commit emitido por `git-keeper` referenciando `(SPEC-002)`
