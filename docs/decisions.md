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

## [INSTITUTED] ADR-006 — Pydantic frozen + strict + extra-forbid

- Date: 2026-05-19
- Status: INSTITUTED
- Context: Entities OData são lidas-de-API; queremos imutabilidade pra evitar mutação acidental e detecção early de schema drift (campo novo do servidor).
- Decision: `ODataEntity` base com `frozen=True, strict=True, extra="forbid"`. Todas entidades herdam.
- Consequences: schema drift quebra teste imediatamente (extra forbid). Frozen impede dataclass-style mutation; uso explicito de `model_copy(update=...)` quando precisar variante.

## [INSTITUTED] ADR-008 — Notion MCP sync via notion-curator only

- Date: 2026-05-19
- Status: INSTITUTED
- Context: Queremos manter `specs/`, `docs/`, `AGENTS.md` espelhados em pages Notion pra colaborar com humanos que não vivem no repo. Notion expõe um MCP server oficial (`@notionhq/notion-mcp-server`) que dá acesso CRUD a pages. Sem disciplina, qualquer agente passa a escrever no Notion e a divergir.
- Decision: Único agente autorizado a invocar MCP `notion` write é o `notion-curator`. Outros agentes que queiram push/pull imprimem `[NOTION_REQUEST] <msg>` e o primary delega.
- Implementation:
  - `.opencode/mcp.json` declara o server com `transport: stdio` e env via `${NOTION_TOKEN}`, `${NOTION_ROOT_PAGE_ID}`.
  - Permission MCP em `.opencode/agents/notion-curator.md` contém `mcp: { notion: allow }`. Nenhum outro agent tem essa chave (HR-22).
  - Audit grep em `scripts/audit.sh` valida que nenhum outro agente referencia `mcp:` com `notion`.
  - Conflict resolution: hash sha256 do conteúdo (sem headers) compara contra `last-sync-hash` no header HTML do md. Disk wins por default; conflict explicito exige flag humana.
- Consequences:
  - Notion vira segunda fonte visível (read-only para humano "não-dev").
  - Risco: se humano editar a page no Notion UI sem rodar `/notion-sync pull`, próximo `push` aborta com `[NOTION_CONFLICT]`. Workflow esperado: edit -> pull -> commit -> push.
  - Rate limit Notion MCP ~3 RPS; cliente self-throttle 5 RPS máximo.
- Rollback: desabilitar removendo permission MCP do `notion-curator` e bloco `mcpServers.notion` do `.opencode/mcp.json`. Specs/docs continuam no disco normalmente; Notion vira read-only manual.
