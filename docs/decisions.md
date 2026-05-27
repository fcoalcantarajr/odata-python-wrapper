<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# Decisions

Formato: `[INSTITUTED]` (humano confirmou) ou `[CANDIDATE]` (proposed by retrospector).

## [INSTITUTED] ADR-001 — OData v4.0-preview default

- Date: 2026-05-19
- Status: INSTITUTED
- Context: ADO Analytics expoe v2.0 (stable) e v4.0-preview. v4.0-preview tem entity sets novos (e.g. `WorkItemBoardSnapshot`), schema mais coerente, e suporte futuro garantido pela MS. v2.0 vai sair de produção num horizonte não publicado.
- Decision: usar `v4.0-preview` como default. `ODATA_VERSION` é single source of truth (`client.py`).
- Rollback: trocar para `v2.0` exige (a) amend desta ADR para INSTITUTED v2.0, (b) atualizar fixture `odata_version` em `tests/conftest.py` (parametrize) e re-rodar suite inteira, (c) revisar specs SPEC-009/010 (entidades) que mencionam entity sets exclusivos de v4.0.
- Consequences: protocolo "preview" implica risk de breaking change. Mitigado por: testes parametrizáveis em ambas versões, audit grep impede literal `_odata/v2.0` em `src/`.

## [INSTITUTED] ADR-002 — Auth error mapping (PAT inválido → AuthenticationError)

- Date: 2026-05-19
- Status: INSTITUTED
- Context: Azure DevOps retorna HTTP 203 + text/html quando PAT é inválido/expirado, e 401 quando PAT não tem permissão. O client precisa mapear ambos pra uma exceção clara e nunca retry.
- Decision: `parse_response()` em `_http.py` detecta 203+text/html antes de qualquer outro status, levantando `AuthenticationError`. 401 também levanta `AuthenticationError`. Ambos NÃO são subclasses de `TransientError`, então tenacity nunca retry.
- Consequences: Hierarquia de exceções: `AdoODataError` → `AuthenticationError`, `BadRequestError`, `TransientError` (→ `RateLimitError`). PAT mascarado com `pat[:6] + "..."` em logs (HR-16).

## [INSTITUTED] ADR-003 — Retry strategy (tenacity expo+jitter, só TransientError)

- Date: 2026-05-19
- Status: INSTITUTED
- Context: Rate limiting (429) e erros 5xx são transitórios; 400 e 401/203 são permanentes. Precisamos de backoff exponencial com jitter, cap de tentativas, e stop condition especial para RateLimitError.
- Decision: `with_retry()` em `retry.py` usa `tenacity.retry_if_exception_type(TransientError)` — só retry em 5xx e 429. `RateLimitError` capped em min(max_attempts, 3). `wait_exponential_jitter(initial=0.5, max=10.0)`. Reraise sempre. Before-sleep log em WARNING.
- Consequences: AuthenticationError/BadRequestError atravessam sem retry. RateLimitError respeita Retry-After via jitter. Máximo 3 tentativas pra 429, configurável pra 5xx via `max_attempts`.

## [INSTITUTED] ADR-004 — Pagination async iterator ($skip/$top + @odata.nextLink)

- Date: 2026-05-19
- Status: INSTITUTED
- Context: Azure DevOps OData suporta `$skip`/`$top` para paginação offset-based, e opcionalmente `@odata.nextLink` para cursor-based. Precisamos de um iterador async que funcione com ambos.
- Decision: `iter_pages()` em `pagination.py` começa com `$skip=0`, incrementa pelo tamanho real de cada página. Se `@odata.nextLink` aparecer na resposta, segue o link (URL absoluto) em vez de calcular skip. Se uma página tem menos items que `$top` E não tem nextLink, iteração termina.
- Consequences: Page size default = 100. Query options passadas como dict opcional (mesclado com $skip/$top). Cliente expõe via `client.paginate(entity_set, top=..., query=...)`.

## [INSTITUTED] ADR-005 — Filter DSL (expression tree com escape)

- Date: 2026-05-19
- Status: INSTITUTED
- Context: $filter é a query option mais complexa do OData, com operadores de comparação, `and`/`or`/`not` lógicos, e função `contains`. Strings precisam de escape de aspa simples (HR-12 gotcha 6).
- Decision: `Filter` em `query/_filter.py` é uma tree de nós imutáveis com método `build()`. Fábricas estáticas: `eq`, `ne`, `and_`, `or_`, `not_`, `contains`. Escape de aspa simples por duplicação (`O'Keefe` → `O''Keefe`). Datetime em ISO 8601 sem prefixo `datetime'` (HR-11 gotcha 7).
- Consequences: `Filter.build()` retorna string limpa. Composição via `Filter.and_(a, b)` ou `Filter.or_(a, b)` com parênteses automáticos.

## [INSTITUTED] ADR-006 — Pydantic frozen + strict + extra-forbid

- Date: 2026-05-19
- Status: INSTITUTED
- Context: Entities OData são lidas-de-API; queremos imutabilidade pra evitar mutação acidental e detecção early de schema drift (campo novo do servidor).
- Decision: `ODataEntity` base com `frozen=True, strict=True, extra="forbid"`. Todas entidades herdam.
- Consequences: schema drift quebra teste imediatamente (extra forbid). Frozen impede dataclass-style mutation; uso explicito de `model_copy(update=...)` quando precisar variante.
## ADR-009: Notion MCP como store canônico de specs + ADRs

- **Date:** 2026-05-19
- **Status:** Accepted
- **Context:** Precisamos de um store central que o Agente Omo leia e escreva, sem depender de git. Notion foi escolhido porque o Omo tem MCP nativo e todos os ADRs + specs precisam ser acessíveis a stakeholders não-técnicos.
- **Decision:** Usar `opencode-mcp-notion` com token OAuth e workspace ID. `notion-curator` é o único agente autorizado a escrever no Notion (HR-22). Demais agentes imprimem `[NOTION_REQUEST]` e param.
- **Consequences:** Positivo: stakeholders não-técnicos veem specs; Notion search funciona cross-workspace. Negativo: sync bidirecional requer disciplina; se token expirar, Omo escala.

## ADR-010: Scaffolding da entrega via opencode (Steps 1-10)

- **Date:** 2026-05-19
- **Status:** Accepted
- **Context:** O repository estava vazio. Precisávamos de todos os arquivos de infra (pyproject, ruff, mypy, pre-commit, scripts, configs, CI) e de engenharia (specs, docs, ADRs, handoff) antes de escrever qualquer código de domínio. Fazer manualmente levaria dias.
- **Decision:** Usar opencode plus Notion MCP como bootstrap engine. Cada "Step" do Notion vira um comando / arquivo no repositório. O supervisor (`opencode`) lê a página raiz no Notion, itera sobre as 10 subpáginas (Steps), e para cada uma extrai o conteúdo e materializa em disco.
- **Consequences:** Positivo: repositório materializado em < 20 min; rastreabilidade via conventional commit; ADR-009 registrado. Negativo: dependência de Notion MCP disponível; se Notion ficar offline, bootstrap não roda.

## [INSTITUTED] ADR-007 — Query serialization order (HR-9)

- **Date:** 2026-05-19
- **Status:** INSTITUTED
- **Context:** Azure DevOps Analytics OData exige ordem fixa de query options: `$apply → $filter → $orderby → $expand → $select → $skip → $top`. Qualquer ordem diferente retorna 400.
- **Decision:** `serialize()` em `query/_serialize.py` impõe a ordem canônica independente da ordem de inserção no dict. Opções não-canônicas são anexadas ao final na ordem de inserção. `None` e `""` são filtrados. URL-encoding usa `%20` (não `+`).
- **Consequences:** `AdoODataClient.get()` e `iter_pages()` passam dict direto pro serializer; URL é construída como `f"{service_root}/{entity_set}?{serialized_query}"`.

## [INSTITUTED] ADR-008 — Batch POST para URLs longas (HR-10)

- **Date:** 2026-05-19
- **Status:** INSTITUTED
- **Context:** URLs OData com $filter enorme podem exceder 3000 chars. Azure DevOps rejeita URLs > 3000 chars. A solução é `POST $batch` multipart/mixed com a query no body.
- **Decision:** `maybe_batch()` em `query/_batch.py` verifica o tamanho da query serializada. Se > 3000 chars, switcha para POST com Content-Type `multipart/mixed` e `$batch` endpoint. O body contém um changeset com método GET e a query original.
- **Consequences:** Transparente pro caller — `client.get()` decide quando usar batch. Parsing de resposta batch via `parse_batch_response()` extrai o JSON do multipart response.

## [INSTITUTED] ADR-011 — Fluent API QueryBuilder

- **Date:** 2026-05-23
- **Status:** INSTITUTED
- **Context:** Após 8 specs de DSLs baixo nível (Filter, Apply, serialize, batch), usuários precisam de uma API fluente que componha todas elas sem conhecer detalhes de serialização.
- **Decision:** `QueryBuilder` em `query/_builder.py` com setters imutáveis (cada um retorna nova instância). Métodos: `.filter()`, `.select()`, `.top()`, `.skip()`, `.orderby()`, `.expand()`, `.apply()`. Terminal: `.get()` (retorna dict) e `.paginate()` (async iterator). Fábrica via `client.query(entity_set)`.
- **Consequences:** Chamadas encadeadas: `client.query("WorkItems").filter(...).select(...).top(10)`. `str(builder)` serializa com `serialize()` respeitando HR-9. Imutabilidade garantida por deepcopy interno.

## [CANDIDATE] ADR-012 — Doc-API alignment validation (doc-check gate)

- **Date:** 2026-05-27
- **Status:** CANDIDATE (proposed by retrospector)
- **Context:** Documentation fix cycle F1–F9 revealed that doc examples diverged
  from the approved spec (`specs/006-apply-dsl.md`) and from the actual source
  code API. No existing gate catches mismatches between docs and code. Examples:
  `aggregate("Sum", "Effort")` (inverted args), `Count` as method name (should
  be `countdistinct`), inconsistent `load_dotenv()` pattern.
- **Decision (proposed):** Adicionar um gate opcional de "doc-check" que extrai
  trechos de código Python de arquivos `.md` em `docs/` e valida que as chamadas
  de API correspondem à assinatura real dos métodos em `src/`. Idealmente como
  script em `scripts/doc-check.sh` ou hook de pre-commit.
- **Consequences (proposed):** Previne rework cíclico de documentação. Usuários
  seguem exemplos que realmente funcionam. Custo de implementação: ~1 dia para
  script inicial de extração + validação.
- **Riscos (proposed):** Pode gerar falsos positivos se doc usa pseudo-código ou
  variações intencionais. Mitigação: ignorar blocos marcados com
  `# doc-check: skip`.

## ADR-013 [CANDIDATE] — Paginator max-pages guard (F6(b))

- **Date:** 2026-05-27
- **Status:** CANDIDATE (proposed by spec-author review)
- **Context:** `client.paginate()` uses an unbounded `while True` loop that can
  theoretically run indefinitely if ADO returns non-empty pages forever.
  Intern hit a 60s timeout with large datasets.
- **Decision (proposed):** Postpone implementation. Requires a formal spec
  (`specs/NNN-paginate-max-pages.md`) before any `src/` change (HR-1).
- **Rationale:** The doc-only fix (unbounded warning in cookbook Recipe 4) was
  applied as F6(a). Library enhancement (optional `max_pages` parameter +
  `ClientTimeout` default) needs proper spec with acceptance criteria scoped
  to pagination, not general DSL.