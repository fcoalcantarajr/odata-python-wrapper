# AGENTS.md — ado-odata-async

Client Python async pro Azure DevOps Analytics OData (Work Tracking).
Lido pelo opencode no início de cada sessão. Curto, estável, verificável.

---

## STACK (PIN)

- Python **3.12** com **`uv`** (NUNCA `pip` direto, NUNCA `python` direto — use `uv run`).
- `aiohttp>=3.13`, `pydantic>=2.8` (frozen+strict), `tenacity>=9.0`, `python-dateutil`, `yarl`.
- `pytest>=8`, `pytest-asyncio>=0.24`, `aioresponses>=0.7`, `hypothesis>=6.112`, `pytest-cov`.
- `ruff>=0.6`, `mypy>=1.11 --strict`, `pre-commit>=4.0`.
- OData **`v4.0-preview`** — endpoint `_odata/v4.0-preview/` (ADR-001).

---

## SDLC (SDD + TDD, sequência obrigatória por feature)

1. **SPEC** — `/spec` ou humano escreve `specs/NNN-<slug>.md` (User Story + Use Cases + Gherkin AC absoluto + INVEST ≥ 8/10).
2. **SPEC_CHECK** — `/spec-check` invoca `spec-author`. Veredito APPROVED / ADJUSTMENTS / REQ_BLOCKED.
3. **TEST_RED** — `/test-first` invoca `atlas` (omo). Escreve `tests/unit/test_<slug>.py` que FALHA. NÃO toca `src/`.
4. **IMPL_GREEN** — `/implement` invoca `hephaestus` (omo). Escreve código mínimo em `src/` pra virar GREEN.
5. **REVIEW** — `/review` invoca `oracle` (omo) + `odata-reviewer` (custom). Read-only.
6. **COMMIT** — `/commit` invoca `git-keeper`. 4-stage gate. Conventional Commits.
7. **NOTION_SYNC** — push automático após /commit (`notion-curator` via Notion MCP).
8. **RETRO** (a cada 3-4 specs) — `/retro` invoca `retrospector`.

Nenhum passo é pulado. TEST_RED VEM ANTES DO IMPL_GREEN. SEMPRE.

---

## HARD RULES

- **HR-1** Toda feature começa com spec em `specs/NNN-<slug>.md` aprovado por `/spec-check`. Sem spec aprovado, `src/` NÃO é tocado.
- **HR-2** Toda dependência via `uv add` no `pyproject.toml`. `pip install` é FORBIDDEN.
- **HR-3** **Test first, always.** Nenhum arquivo em `src/` é editado sem teste falho em `tests/unit/`. `test-first-guard` confirma RED antes de `hephaestus` rodar.
- **HR-4** Pydantic models são `model_config = ConfigDict(frozen=True, strict=True)`. Nada de `BaseModel` mutável.
- **HR-5** Tipagem **estrita** sempre. `# type: ignore` é FORBIDDEN exceto com `# type: ignore[<code>]  # reason: <texto>`.
- **HR-6** Async-only no client. NUNCA `requests`, NUNCA `urllib`. Tudo via `aiohttp`.
- **HR-7** **Single `ClientSession` por client.** Criada em `__aenter__`, fechada em `__aexit__`. Re-entry forbidden.
- **HR-8** Auth via `aiohttp.BasicAuth("", pat)` — **username vazio**. Qualquer valor retorna 401 (gotcha 1).
- **HR-9** Query option order via `query/_serialize.py` only. Ordem: `$apply → $filter → $orderby → $expand → $select → $skip → $top`.
- **HR-10** URLs `> 3000 chars` → switch automático pra `POST $batch` multipart/mixed. Limite checado no serializer.
- **HR-11** Datetime literals em filtros: ISO 8601 com `Z` ou offset, SEM prefixo `datetime'...'` (gotcha 7).
- **HR-12** Escape de aspa simples em filtros: dobra (`O'Keefe` → `'O''Keefe'`) (gotcha 6).
- **HR-13** `WorkItemSnapshot` / `WorkItemBoardSnapshot` REQUEREM `$apply` com `groupby` em `DateSK`/`DateValue` (gotcha 4).
- **HR-14** `$expand=Revisions` BLOQUEADO → usar entity set `WorkItemRevisions` (gotcha 5).
- **HR-15** HTTP 203 + `text/html` = PAT inválido → `AuthenticationError`, **não retry** (gotcha 8).
- **HR-16** PAT mascarado em logs: nunca printar mais que 6 primeiros chars + `...`.
- **HR-17** **Subagents não invocam subagents.** opencode hardcoda `task: false` em sessão subagent (Issue #7296). Hierarquia flat: PRIMARY → SUBAGENT.
- **HR-18** **Apenas `git-keeper` toca git.** Outros agentes imprimem `[GIT_REQUEST] <msg>` e param. Audit: `grep -rnE '\\bgit (commit|push|pull|merge|rebase|add|reset|checkout|tag)\\b' .opencode/agents/ | grep -v git-keeper.md` deve ser vazio.
- **HR-19** OData version isolada em `client.py` como `ODATA_VERSION = "v4.0-preview"`. Mudança de versão requer ADR novo.
- **HR-20** `pyproject.toml` é a única fonte de verdade da versão do package; código lê via `importlib.metadata.version(__package__)`.
- **HR-21** Coverage mínimo: `--cov-fail-under=85`. CI quebra abaixo disso.
- **HR-22** **Apenas `notion-curator` invoca MCP `notion`.** Outros imprimem `[NOTION_REQUEST] <msg>` e param. Audit: `grep -rni 'mcp.*notion' .opencode/agents/ | grep -v notion-curator.md` deve ser vazio.

---

## FORBIDDEN tokens (greps em `scripts/audit.sh`)

- `# type: ignore` sem código específico nem comentário `# reason:` → BLOCK
- `as Any` ou `: Any` fora de stubs/protocols → WARN
- `pip install` em qualquer `.sh` ou `.md` (use `uv add` / `uv sync`) → BLOCK
- `python ` ou `python3 ` direto invocando script (use `uv run python`) → BLOCK
- `BasicAuth(<qualquer-coisa-não-vazia>, pat)` → BLOCK (HR-8 gotcha 1)
- `datetime'` literal em filtro OData → BLOCK (HR-11 gotcha 7)
- `$expand=Revisions` literal → BLOCK (HR-14 gotcha 5)
- `requests.` ou `urllib.` em `src/` → BLOCK (HR-6)
- `print(.*pat` (sem mascaramento) → BLOCK (HR-16)
- `_odata/v2.0` literal em `src/` → BLOCK (HR-19; v4.0-preview only)

---

## Audit.sh Enforcement Notes

**HR-13 (WorkItemSnapshot groupby)**:  
HR-13 validation is enforced **by code** (`_check_snapshot_groupby()` in `src/ado_odata_async/query/_apply.py`) at query serialization time. See function docstring for detailed rationale. Violations fail immediately with a descriptive error, preventing silent bugs at the API level.

**Other code-only HRs** (HR-9, HR-11, HR-12, HR-16, HR-19): Enforced at code level; `audit.sh` is a first-line gate for easy-to-catch patterns, not exhaustive OData domain validation.

---

## File ownership

| Path                    | Quem escreve                              | Quem NÃO escreve                |
| ----------------------- | ----------------------------------------- | ------------------------------- |
| `specs/*.md`            | humano, `spec-author`                     | todos os outros                 |
| `tests/unit/*.py`       | `atlas` (omo)                             | `hephaestus`                    |
| `tests/integration/*.py`| `atlas` (omo)                             | `hephaestus`                    |
| `src/**/*.py`           | `hephaestus` (omo)                        | `atlas`                         |
| `docs/*.md`             | `librarian` (omo), `retrospector`         | —                               |
| `AGENTS.md`             | humano (apenas)                           | TODOS os agentes                |
| `.opencode/**`          | humano (apenas)                           | TODOS os agentes                |
| `pyproject.toml`        | `hephaestus` (via `uv add`)               | manual exceto config            |
| `git index/HEAD`        | `git-keeper`                              | TODOS os outros (HR-18)         |
| MCP `notion` (write)    | `notion-curator`                          | TODOS os outros (HR-22)         |

---

## DoD universal por commit

- [ ] Spec aprovado (`/spec-check` → APPROVED)
- [ ] Teste RED escrito antes do código (`test-first-guard` → CONTINUE)
- [ ] `uv run pytest -q` GREEN
- [ ] `uv run ruff check .` clean
- [ ] `uv run mypy src/` strict clean
- [ ] `uv run pytest --cov=ado_odata_async --cov-fail-under=85` GREEN
- [ ] `bash scripts/audit.sh` exit 0
- [ ] AC do spec todos cobertos
- [ ] Conventional Commit (`feat|fix|chore|docs|test|refactor|perf|ci`)

---

## 8 gotchas críticas (verbatim — Azure DevOps Analytics OData)

Valem pra v2.0 e v4.0-preview — são restrições do serviço, não da versão.

1. **PAT auth**: username MUST be empty (`""`). Qualquer valor retorna 401.
2. **Query option order**: `$apply → $filter → $orderby → $expand → $select → $skip → $top`. Ordem errada = 400.
3. **URL > 3000 chars** → switch pra `POST $batch` multipart/mixed.
4. **`WorkItemSnapshot` / `WorkItemBoardSnapshot`** REQUEREM `$apply` com `groupby` em `DateSK`/`DateValue`.
5. **`$expand=Revisions` BLOQUEADO** → usar entity set `WorkItemRevisions`.
6. **Escape de aspa simples**: dobre (`O'Keefe` → `'O''Keefe'`).
7. **Datetime literals**: ISO 8601 com `Z` ou offset, SEM prefixo `datetime'...'`.
8. **HTTP 203 + `text/html`** = PAT inválido → `AuthenticationError`, **não retry**.

---

## Logging convention

- Logger por módulo: `logger = logging.getLogger(__name__)`.
- Nunca `print()` em `src/` (use logger).
- PAT mascarado: `pat[:6] + "..."` (HR-16).
- Nível default: `INFO`. `DEBUG` libera request/response (com PAT mascarado).
- Em testes: `caplog.set_level(logging.DEBUG)` quando precisar inspecionar.

---

## Governance — quando o omo escala (imprime `[ESCALATION] <reason>`)

- DoD failed 3x consecutivas no mesmo spec.
- External dependency unreachable (Azure DevOps API down, Notion MCP timeout).
- Plan would modify `AGENTS.md` ou `.opencode/**`.
- Spec INVEST < 6.
- Git conflict markers detectados.
- v4.0-preview breaking change detected (rollback do spec afetado pra v2.0 via override + ADR novo).
- Notion sync conflict (`/notion-sync` detectou drift simultâneo).
- Notion MCP unauthenticated (token OAuth expirou).

Em qualquer `[ESCALATION]`: agente para, imprime razão, espera humano decidir.
