---
name: git-discipline
description: 4-stage commit gate + Conventional Commits + sync via pull-rebase-autostash. Use no `/commit` e `/sync`. Apenas `git-keeper` executa (HR-18).
---

# Git discipline

Apenas `git-keeper` toca git (HR-18). Outros: `[GIT_REQUEST]`.

## 4-stage commit gate

1. **Diff scope** — `git diff --stat` mostra apenas arquivos do spec.
2. **Pytest GREEN** — `uv run pytest -q` + cov ≥ 85%.
3. **Static gates** — `ruff`, `mypy --strict`, `audit.sh` exit 0.
4. **AC coverage** — cada AC do spec tem teste com `AC-N` referenciado.

Qualquer falha → aborta com razão, não commit.

## Conventional Commits

Formato:
```
\<type\>(\<scope\>): \<short\> (SPEC-NNN)
\<body opcional\>
```

Types: `feat | fix | chore | docs | test | refactor | perf | ci | build | style`.

Exemplos:
- `feat(http): single ClientSession lifecycle on v4.0-preview (SPEC-001)`
- `test(http): RED AC-1..AC-7 for session lifecycle (SPEC-001)`
- `fix(query): correct $filter ordering (SPEC-007)`
- `docs(adr): ADR-008 Notion MCP sync (SPEC-012)`

## /sync

```
git fetch origin
git pull --rebase --autostash
uv run pytest -q   # confirma GREEN após rebase
git push
```

Conflict markers → `[ESCALATION]`, humano resolve.

## Forbidden

- `git push --force` (NUNCA).
- `git commit --no-verify` (NUNCA; quebra pre-commit hook).
- `git rebase -i` interativo autônomo (só humano).