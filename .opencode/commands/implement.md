---
agent: hephaestus
subtask: true
description: Escreve código mínimo em `src/` pra virar GREEN os testes do spec. Refactor só se HARD RULE violada. Pre-requisito: test-first-guard retornou CONTINUE.
---

Pre-requisito: `test-first-guard` confirmou RED em `tests/unit/test_<slug>.py`.

**Spec:** $ARGUMENTS

Conteúdo:
@$ARGUMENTS

Procedimento:
1. Localize os testes RED em `tests/unit/test_<slug>.py`.
2. Escreva código mínimo em `src/ado_odata_async/` que faça esses testes virarem GREEN.
3. Respeite TODAS as HARD RULES do `AGENTS.md` (especialmente HR-7 single session, HR-8 BasicAuth empty, HR-9 query order, HR-19 v4.0-preview).
4. Rode `uv run pytest -q tests/unit/test_<slug>.py` até GREEN.
5. Rode `uv run ruff check . && uv run mypy src/ && bash scripts/audit.sh` antes de retornar.
6. Imprima o sumário: arquivos editados em `src/`, todos os testes do spec GREEN.

NÃO escreva teste novo (é com `atlas`). NÃO chame git.
