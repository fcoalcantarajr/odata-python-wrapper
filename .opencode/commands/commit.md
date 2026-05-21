---
agent: git-keeper
subtask: true
description: Roda o 4-stage commit gate e gera commit Conventional para a spec atual. Argumento: SPEC-NNN.
---

Commit da spec atual.

**Spec id:** $ARGUMENTS

Procedimento (qualquer falha aborta com razão):
1. **Stage 1** — `git diff --stat` mostra apenas arquivos esperados pela spec.
2. **Stage 2** — `uv run pytest -q` exit 0; `uv run pytest --cov=ado_odata_async --cov-fail-under=85` exit 0.
3. **Stage 3** — `uv run ruff check .` exit 0; `uv run mypy src/` exit 0; `bash scripts/audit.sh` exit 0.
4. **Stage 4** — cada AC do spec tem teste referenciando `AC-N`.
5. Gere mensagem Conventional: `<type>(<scope>): <short> ($ARGUMENTS)`.
6. `git add` apenas os arquivos do diff stat aprovado, `git commit -m "..."`.
7. Imprima `[NOTION_PUSH_REQUEST] specs/<id>.md, docs/decisions.md, AGENTS.md` pra o primary delegar pro `notion-curator`.
