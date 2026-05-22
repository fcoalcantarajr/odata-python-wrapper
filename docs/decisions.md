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