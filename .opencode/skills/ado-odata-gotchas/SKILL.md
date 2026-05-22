---
name: ado-odata-gotchas
description: 8 gotchas críticas do Azure DevOps Analytics OData (v2.0 e v4.0-preview). Use quando montar request, escrever filtro, expandir entidade, ou debugar 400/401/203 do serviço.
---

# ADO Analytics OData — 8 gotchas (WRONG / CORRECT)

Valem para ambas versões (v2.0 e v4.0-preview). São restrições de serviço.

## Gotcha 1 — PAT auth: username MUST be empty

**WRONG:**
```
auth = aiohttp.BasicAuth("user@example.com", pat)  # 401
```
**CORRECT:**
```
auth = aiohttp.BasicAuth("", pat)  # OK
```

## Gotcha 2 — Query option order

Ordem obrigatória na URL: `$apply → $filter → $orderby → $expand → $select → $skip → $top`.

**WRONG:** `?$select=Id&$filter=State eq 'Active'` (select antes de filter) → 400.
**CORRECT:** `?$filter=State eq 'Active'&$select=Id`.

Isola em `query/_serialize.py` que sempre emite na ordem canônica (HR-9).

## Gotcha 3 — URL > 3000 chars → POST $batch

Limite efetivo ~3000 chars. Acima, switch pra `POST /$batch` multipart/mixed.

```
POST /myorg/myproject/_odata/v4.0-preview/\$batch
Content-Type: multipart/mixed; boundary=batch_\<uuid\>
--batch_\<uuid\>
Content-Type: application/http
Content-Transfer-Encoding: binary
GET WorkItems?\$filter=... HTTP/1.1
Accept: application/json
--batch_\<uuid\>--
```

## Gotcha 4 — WorkItemSnapshot / WorkItemBoardSnapshot exigem $apply

**WRONG:** `?$filter=DateValue gt 2025-01-01` direto → 400.
**CORRECT:** `?$apply=filter(DateValue gt 2025-01-01)/groupby((DateSK), aggregate(...))`.

Checar em build-time: se entity é Snapshot e não tem `$apply` com `groupby` em `DateSK`/`DateValue` → erro do client antes de mandar (HR-13).

## Gotcha 5 — $expand=Revisions BLOQUEADO

**WRONG:** `?$expand=Revisions` → 400.
**CORRECT:** consultar entity set `WorkItemRevisions` direto, com filtro `WorkItemId eq <id>` (HR-14).

## Gotcha 6 — Escape de aspa simples em filtro

**WRONG:** `?$filter=AssignedTo/UserName eq 'O'Keefe'` → 400.
**CORRECT:** `?$filter=AssignedTo/UserName eq 'O''Keefe'` (aspa simples dobrada) (HR-12).

## Gotcha 7 — Datetime literals SEM prefixo

**WRONG:** `?$filter=ChangedDate gt datetime'2025-01-15T00:00:00Z'` → 400.
**CORRECT:** `?$filter=ChangedDate gt 2025-01-15T00:00:00Z` (sem prefixo `datetime`) (HR-11).

## Gotcha 8 — HTTP 203 + text/html = PAT inválido

Quando PAT é inválido, ADO retorna `203 Non-Authoritative` com `Content-Type: text/html` (sign-in page). Não retry.

```
if resp.status == 203 and "text/html" in resp.headers.get("Content-Type", ""):
    raise AuthenticationError("PAT invalid (203 + text/html)")
```

## Nota v4.0-preview vs v2.0

Todas 8 gotchas valem em ambas versões. Diferenças entre versões ficam no schema (entity sets, navigation properties), não nessas restrições de protocolo.