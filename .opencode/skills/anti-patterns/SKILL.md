---
name: anti-patterns
description: Catálogo de anti-patterns observados (AP-NNN). Cresce via `/retro`. Use quando revisar código, escrever spec novo, ou quando algo parece familiar e ruim.
---

# Anti-patterns (AP-NNN)

Cresce via `/retro`. Cada entry: contexto, smell, correção.

## AP-001 — Multiple ClientSession per client

**Smell:** criação de `aiohttp.ClientSession()` fora de `__aenter__`, ou recriada em cada método público.
**Por que ruim:** vaza connectors, dobra DNS lookups, quebra cancel propagation.
**Correção:** única session armazenada em `self._session`, criada em `__aenter__`, fechada em `__aexit__` (HR-7).

## AP-002 — BasicAuth com username não-vazio

**Smell:** `BasicAuth("user@x.com", pat)`.
**Por que ruim:** ADO Analytics retorna 401 (gotcha 1).
**Correção:** `BasicAuth("", pat)` sempre (HR-8).

## AP-003 — Query option em ordem livre

**Smell:** building URL com `f-string` interpolando query options na ordem do código, não na canônica.
**Por que ruim:** ADO Analytics 400 em ordens fora do canônico.
**Correção:** `query/_serialize.py` sempre emite ordem `$apply > $filter > $orderby > $expand > $select > $skip > $top`.

## AP-004 — Spec com Then não-observável

**Smell:** Then "funciona", "é rápido", "é seguro".
**Por que ruim:** sem assertion clara, impossivel virar teste.
**Correção:** Then com status code, igualdade, exceção.

## AP-005 — retry em 401/203 (auth fail)

**Smell:** tenacity retry catch-all incluindo 401, 203.
**Por que ruim:** PAT não vai melhorar com retry; desperdício + atrasa erro.
**Correção:** retry só em 429/5xx; `AuthenticationError` não-retryável (HR-15).

*(retrospector adiciona AP-006+ ao longo do tempo)*