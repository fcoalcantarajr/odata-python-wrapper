<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# 🚌 Handoff — ado-odata-async

> Se o desenvolvedor original for atropelado por um ônibus, ler este arquivo antes de qualquer ação.

---

## Single source of truth

1. **`AGENTS.md`** ([AGENTS.md](../AGENTS.md)) — regras, stack, gotchas, DoD. Sempre a primeira leitura.
2. **`pyproject.toml`** — versão do package (lida via `importlib.metadata.version`). Nenhum outro lugar duplica.
3. **`specs/`** — backlog e specs aprovadas. Nenhuma implementação sem spec aprovada.
4. **`docs/decisions.md`** — ADRs registrados. Vale mais que conversa de Slack.
5. **`.opencode/`** — comandos, agentes, skills. Cada comando invoca exatamente um subagent.

---

## Fluxo diário (loop)

```
1. /spec-check <spec> → APPROVED?
2. /test-first <spec> → RED (atlas escreve testes)
3. /implement <spec> → GREEN (hephaestus implementa)
4. /review <spec> → APPROVED (oracle + odata-reviewer)
5. /commit → git-keeper 4-stage gate
6. /notion-sync → notion-curator push
```

Cada ciclo leva ~30-60 min. Faça 3-4 ciclos por dia.

---

## 8 gotchas que vão te pegar

Verbatim de `AGENTS.md`:

| # | Gotcha | Solução |
|---|--------|---------|
| 1 | PAT auth username vazio | `BasicAuth("", pat)` — qualquer valor retorna 401 |
| 2 | Query option order | `$apply → $filter → $orderby → $expand → $select → $skip → $top` |
| 3 | URL > 3000 chars | Switch pra `POST $batch` multipart/mixed |
| 4 | WorkItemSnapshot sem $apply groupby | Requer `groupby(DateSK)` |
| 5 | $expand=Revisions bloqueado | Use entity set `WorkItemRevisions` |
| 6 | Escape aspa simples | Dobre: `O'Keefe → O''Keefe` |
| 7 | Datetime literal sem prefixo | ISO 8601 com Z ou offset, sem `datetime'...'` |
| 8 | HTTP 203 + text/html | PAT inválido → `AuthenticationError`, não retry |

---

## Árvore do repositório

```
.
├── AGENTS.md                     ← Leia primeiro
├── pyproject.toml                ← Versão, dependências (uv sync, pip forbidden)
├── .opencode/
│   ├── agents/                   ← 6 subagents (spec-author, test-first-guard, odata-reviewer, git-keeper, retrospector, notion-curator)
│   ├── commands/                 ← 9 comandos (/spec, /spec-check, /test-first, /implement, /review, /commit, /sync, /retro, /notion-sync)
│   └── skills/                   ← 7 skills (spec-driven-development, tdd-loop, ado-odata-gotchas, anti-patterns, asyncio-patterns, git-discipline, notion-sync)
├── src/ado_odata_async/          ← Código Python (12+ módulos)
│   ├── __init__.py, auth.py, client.py, exceptions.py, retry.py, pagination.py, metadata.py
│   ├── query/ (DSLs: filter, apply, serialize)
│   └── entities/ (WorkItem, WorkItemRevisions, etc.)
├── specs/
│   ├── 000-TEMPLATE.md           ← Template canônico
│   ├── 001-http-skeleton.md      ← Primeira spec real
│   └── BACKLOG.md                ← Próximas 12 specs
├── tests/                        ← unit (pytest-asyncio + aioresponses)
├── docs/
│   ├── architecture.md           ← Visão geral do sistema
│   ├── decisions.md              ← ADRs
│   └── HANDOFF.md                ← Este arquivo
├── scripts/
│   └── audit.sh                  ← Verificador de FORBIDDEN tokens (HR)
└── .devcontainer/
    └── postCreate.sh             ← Bootstrap do devcontainer
```

---

## Comandos opencode

| Comando | O que faz | Subagent invocado |
|---------|-----------|-------------------|
| `/spec <slug>` | Gera spec a partir do template | spec-author |
| `/spec-check <slug>` | Valida spec contra critérios INVEST | spec-author |
| `/test-first <slug>` | Escreve testes RED (NUNCA toca src/) | atlas → test-first-guard |
| `/implement <slug>` | Implementa código mínimo pra GREEN | hephaestus |
| `/review <slug>` | Review de spec + implementação | oracle + odata-reviewer |
| `/commit` | 4-stage gate: lint → type → test → audit | git-keeper |
| `/sync` | uv sync + pre-commit | — (shell) |
| `/retro` | Retrospectiva a cada 3-4 specs | retrospector |
| `/notion-sync` | Push specs + decisions + AGENTS pra Notion | notion-curator |

---

## Primeiras ações do sucessor

1. `uv sync` (instala dependências)
2. `uv run pytest -q` (deve passar — se não, correção emergencial)
3. `uv run ruff check .` (lint limpo)
4. `uv run mypy src/ --strict` (tipagem limpa)
5. `bash scripts/audit.sh` (exit 0)
6. Pegar a spec mais prioritária de `specs/BACKLOG.md` que esteja `DRAFT`
7. Iniciar ciclo: `/spec-check 001` → `/test-first 001` → `/implement 001` → `/review 001` → `/commit`

---

## Emergency contact

- **Repo owner**: @fcoalcantarajr
- **ADR disputes**: Abrir issue no repo marcando `[ADR]`. Não alterar `docs/decisions.md` sem issue.
- **Notion MCP outage**: Verificar status em https://status.notion.so. Se offline > 1h, pular `/notion-sync` e continuar.
- **Azure DevOps API breaking change**: Pausar. Criar spec de migração. ADR novo obrigatório.