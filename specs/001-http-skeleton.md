<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# SPEC-001: HTTP skeleton (single session + v4.0-preview + empty-user BasicAuth)

- id: SPEC-001
- slug: http-skeleton
- status: IMPLEMENTED
- created: 2026-05-19
- owner: @fcoalcantarajr

## User Story

As a desenvolvedor que vai consumir ADO Analytics, I want um `AdoODataClient` async que abre **uma só** `aiohttp.ClientSession` no `__aenter__` com `BasicAuth("", pat)` e fala com `_odata/v4.0-preview/`, so that eu posso fazer múltiplas chamadas sem vazar conexões e sem cair em 401 por usuário errado nem em 400 por versão errada.

## Use Cases

- UC1: Abrir client e fazer N GETs reaproveitando session.
- UC2: Garantir que sair do `async with` fecha session (sem warning de "unclosed connector").
- UC3: Garantir que URL construída aponta para `v4.0-preview` (não v2.0).

## Acceptance Criteria (Gherkin absoluto)

### AC-1: single ClientSession lifecycle

```
Given um AdoODataClient(org="myorg", project="myproject", pat=fake_pat)
When entro no async with e faço duas chamadas client.get("WorkItems") consecutivas
Then `client._session` é o mesmo objeto antes e depois das duas chamadas (identidade `is`)
```

### AC-2: session fechada no __aexit__

```
Given um AdoODataClient já dentro do async with
When saio do async with
Then `client._session` == None
	And `aiohttp.ClientSession` foi fechada (closed == True antes da nulificação)
	And não há ResourceWarning "Unclosed client session" no stderr capturado
```

### AC-3: BasicAuth com usuário vazio (HR-8)

```
Given um AdoODataClient com pat=fake_pat
When entro no async with
Then a `aiohttp.ClientSession` foi criada com `auth=BasicAuth("", fake_pat)`
	And `auth.login == ""` (exatamente string vazia, não None)
```

### AC-4: URL aponta para v4.0-preview (HR-19)

```
Given um AdoODataClient(org="myorg", project="myproject", pat=fake_pat)
When client.get("WorkItems") é chamado dentro do async with
Then a URL HTTP capturada por aioresponses contém a substring "/_odata/v4.0-preview/WorkItems"
	And NÃO contém "/_odata/v2.0/"
```

### AC-5: ODATA_VERSION é single source of truth (HR-19/HR-20)

```
Given o módulo `ado_odata_async.client`
When importô `ODATA_VERSION`
Then `ODATA_VERSION == "v4.0-preview"` (igualdade exata)
	And nenhum outro arquivo em `src/` contém a string literal `_odata/v4.0-preview` exceto via interpolação de `ODATA_VERSION` (audit grep confirma)
```

### AC-6: entrada dupla no async with falha cedo

```
Given um AdoODataClient já dentro do async with
When tento entrar de novo (`await client.__aenter__()`)
Then é levantada `RuntimeError` com mensagem contendo "already entered"
```

### AC-7: PAT mascarado em repr/str

```
Given um AdoODataClient(pat="abcdef" * 10)
When chamo `repr(client)` ou `str(client)`
Then a saída **não** contém a substring do PAT inteiro
	And contém apenas os 6 primeiros chars do PAT seguidos por "..." (ex: "abcdef...")
```

## NFRs

- **Performance:** N é spec de lifecycle; sem requisito numérico além de "sem vazamento".
- **Security:** PAT nunca aparece inteiro em log, repr, str, ou exception message. `auth.mask_pat` cobre.
- **Observability:** DEBUG log emite `client.entered` e `client.exited` com `odata_version` e PAT mascarado.

## INVEST self-score

- **I**ndependent: 9/10 — não depende de outra spec; SPEC-002+ partem daqui.
- **N**egotiable:  8/10 — detalhes de log podem mudar; lifecycle não.
- **V**aluable:    10/10 — destrava todas as outras specs.
- **E**stimable:   9/10 — lifecycle aiohttp é padrão conhecido.
- **S**mall:       9/10 — ~60 linhas de impl em `client.py` + `auth.py`.
- **T**estable:    10/10 — 7 AC todos observáveis com `aioresponses`.

Média: 9.2/10 → APPROVED-elegible.

## Out-of-scope

- Retry (→ SPEC-003).
- Pagination (→ SPEC-004).
- Query DSL (→ SPEC-005/006/007).
- POST $batch (→ SPEC-008).

## Test plan

- AC-1 → `tests/unit/test_http_skeleton.py::test_ac1_session_reuse`
- AC-2 → `tests/unit/test_http_skeleton.py::test_ac2_session_closed_on_exit`
- AC-3 → `tests/unit/test_http_skeleton.py::test_ac3_basicauth_empty_user`
- AC-4 → `tests/unit/test_http_skeleton.py::test_ac4_url_v4_preview`
- AC-5 → `tests/unit/test_http_skeleton.py::test_ac5_odata_version_single_source`
- AC-6 → `tests/unit/test_http_skeleton.py::test_ac6_double_enter_fails`
- AC-7 → `tests/unit/test_http_skeleton.py::test_ac7_pat_masked_in_repr`

## DoD

- [ ] 7 testes RED escritos por `atlas` via `/test-first`
- [ ] `test-first-guard` retorna CONTINUE
- [ ] `hephaestus` implementa `__aenter__`, `__aexit__`, `get()`, `auth.build_basic_auth`, `auth.mask_pat`
- [ ] 7 testes GREEN
- [ ] Coverage de `client.py` + `auth.py` ≥ 85%
- [ ] `oracle` + `odata-reviewer` ambos APPROVED
- [ ] `git-keeper` 4-stage gate passa
- [ ] Commit: `feat(http): single ClientSession + v4.0-preview + empty-user BasicAuth (SPEC-001)`
- [ ] `notion-curator` push spec + decisions + AGENTS pra Notion