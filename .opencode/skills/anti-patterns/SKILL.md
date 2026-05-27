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

## AP-006 [CANDIDATE] — Nome de método de agregação divergente do serviço ADO

**Contexto:** documentation fix cycle F1–F9 (May 2026). Docs usavam `Count` como
método de agregação (ex.: `aggregate("WorkItemId", "Count")`), mas o Azure DevOps
Analytics só aceita `countdistinct` (minúsculas). Também havia casos de
argumentos invertidos (ex.: `aggregate("Sum", "Effort")`).

**Smell:** usar `Count`, `Sum`, `Average` (capitalizados) como método em
`.aggregate()`, ou inverter a ordem dos argumentos.

**Por que ruim:** ADO Analytics retorna `400 Bad Request` — método `Count` não
existe. A confusão visual entre `Count` (método inexistente) e `Count` (nome de
coluna válido, usado em testes) agrava o problema.

**Correção:** usar sempre `countdistinct`, `sum`, `average`, `min`, `max` —
minúsculas, exatamente como o ADO Analytics aceita. A ordem
`aggregate(field, method)` é canônica: campo primeiro, método depois. Validar
exemplos de docs contra código fonte (`_apply.py`) e contra spec aprovado.

## AP-007 [CANDIDATE] — Doc-API drift (exemplos de documentação inconsistentes
com spec/código)

**Contexto:** documentation fix cycle F1–F9 (May 2026). O spec
`006-apply-dsl.md` já usava ordem canônica correta (`aggregate("Effort", "sum")`),
mas cookbook.md, concepts.md e getting-started.md divergiam — usavam `Count` como
método, invertiam argumentos, ou usavam `load_dotenv()` inconsistente.

**Smell:** documentação escreve exemplos que divergem da API real do código ou do
spec aprovado — sem que nenhum gate detecte a divergência.

**Por que ruim:** gera rework cíclico (corrigir docs → audit → corrigir de novo).
Usuários seguem exemplos errados e recebem `400 Bad Request`. Quebra a confiança
na documentação como fonte confiável.

**Correção:** todo PR de doc deve ser validado contra (a) spec aprovado,
(b) código fonte da API, (c) testes unitários. Adicionar gate opcional de
"doc-check" que extrai exemplos de código de docs e verifica que chamam a API
correta (assinatura, nomes de método, ordem de argumentos).

*(retrospector adiciona AP-008+ ao longo do tempo)*