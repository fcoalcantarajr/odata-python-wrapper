<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# Handoff — primeira iteração end-to-end

Você (o agente primário do opencode + omo) recebeu este repo com tudo pronto:

- `AGENTS.md` na raiz: HARD RULES HR-1..HR-22 e FORBIDDEN tokens.
- `.opencode/agents/`: 6 subagentes (spec-author, test-first-guard, odata-reviewer, git-keeper, retrospector, notion-curator).
- `.opencode/commands/`: 9 commands (`/spec`, `/spec-check`, `/test-first`, `/implement`, `/review`, `/commit`, `/sync`, `/retro`, `/notion-sync`).
- `.opencode/skills/`: 7 skills carregadas on-demand.
- `.opencode-config/`: routing dos modelos free (já copiado pra `~/.config/` pelo postCreate).
- `pyproject.toml`, `src/ado_odata_async/` com stubs `NotImplementedError`, `tests/conftest.py` com fixtures, `docs/architecture.md`, `docs/decisions.md` com ADR-001 + ADR-006.
- `specs/000-TEMPLATE.md`, `specs/001-http-skeleton.md` (já escrita, 7 AC), `specs/BACKLOG.md`.

## Sua missão agora

Fazer SPEC-001 sair de DRAFT pra IMPLEMENTED, ponta-a-ponta, sem perguntar nada que esteja resolvido aqui.

## Sequence obrigatória

1. `/spec-check specs/001-http-skeleton.md`
   - Esperado: `APPROVED`.
   - Se vier `ADJUSTMENTS` ou `REQ_BLOCKED`, pare e me pergunte (humano).

2. `/test-first specs/001-http-skeleton.md`
   - `atlas` escreve `tests/unit/test_http_skeleton.py` com 7 testes RED.
   - Em seguida, você (primary) chama `test-first-guard` com o caminho do spec.
   - Esperado: `CONTINUE`.
   - Se vier `BLOCKED-*`, **não** prossiga pra impl. Reescreva os testes (volta pro `atlas`).

3. `/implement specs/001-http-skeleton.md`
   - `hephaestus` edita `src/ado_odata_async/client.py` e `src/ado_odata_async/auth.py`.
   - Esperado: 7 testes GREEN, `ruff`, `mypy --strict`, `bash scripts/audit.sh` todos exit 0.

4. `/review`
   - Fase 1: `oracle` (async correctness).
   - Fase 2: você (primary) delega pro `odata-reviewer` pra checar HR-7..HR-22 + 8 gotchas.
   - Esperado: ambos `APPROVED`. Se `CHANGES_REQUESTED`, volta pro `hephaestus`.

5. `/commit SPEC-001`
   - `git-keeper` roda o 4-stage gate.
   - Esperado: commit `feat(http): single ClientSession + v4.0-preview + empty-user BasicAuth (SPEC-001)`.
   - Em sucesso, `git-keeper` imprime `[NOTION_PUSH_REQUEST] specs/001-http-skeleton.md, docs/decisions.md, AGENTS.md`.

6. `/notion-sync push specs/001-http-skeleton.md docs/decisions.md AGENTS.md`
   - `notion-curator` espelha as 3 pages no workspace Notion.
   - Esperado: 3 pushed, 0 conflicts.

## Regras que você NÃO pode quebrar

- HR-1..HR-22 (vide `AGENTS.md`). Se humano contradisser, abre `[ESCALATION]`.
- HR-17: você (primary) é o **único** que invoca subagentes. Subagentes não se chamam entre si.
- HR-18: só `git-keeper` toca git. Você ou outros agentes → `[GIT_REQUEST]`.
- HR-22: só `notion-curator` escreve via MCP `notion`. Você ou outros → `[NOTION_REQUEST]`.
- NUNCA edite `src/` antes de teste RED existir e `test-first-guard` retornar `CONTINUE`.
- NUNCA commite sem 4-stage gate verde.
- NUNCA faça `git push --force` ou `git commit --no-verify`.

## Quando parar e perguntar

- `/spec-check` retornou `REQ_BLOCKED`.
- `test-first-guard` retornou `BLOCKED-*` 2x seguidas mesmo com revisão do `atlas`.
- `odata-reviewer` retornou `CHANGES_REQUESTED` 2x seguidas mesmo com fix do `hephaestus`.
- `git-keeper` aborta o gate por razão que você não consegue resolver sozinho.
- `notion-curator` reporta `[NOTION_CONFLICT]`.
- Qualquer modelo free retornou erro irrecuperável (rate limit total, modelo deprecated).

## Quando seguir sem perguntar

- Tudo que cabe em HR-* e em uma das 7 skills.
- Specs DRAFT no `BACKLOG.md` que você já sabe destrancar (depois de SPEC-001 IMPLEMENTED, comece SPEC-002 automaticamente — a menos que humano interrompa).

## Pronável sequence depois de SPEC-001 GREEN

`SPEC-002 → SPEC-007 → SPEC-003 → SPEC-005 → SPEC-006 → SPEC-008 → SPEC-004 → SPEC-009 → SPEC-010 → SPEC-011 → SPEC-012`

A cada 3 specs IMPLEMENTED, rode `/retro HEAD~<n>..HEAD` antes de começar a próxima.

## Tom de relatório

- Imprima sumarios curtos no fim de cada etapa: arquivos editados, testes GREEN, gate result.
- Não repita o que o humano já sabe.
- Se algo não ficou claro na spec, **não invente**: abra `[ESCALATION]`.

## Bom trabalho. Vai.
