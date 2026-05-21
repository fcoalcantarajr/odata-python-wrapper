---
agent: atlas
subtask: true
description: A partir do spec aprovado, escreve `tests/unit/test_<slug>.py` que falha (RED). NÃO toca em `src/`. Em seguida, o primary roda test-first-guard pra confirmar RED.
---

O spec abaixo já foi aprovado por `/spec-check`. Escreva os testes RED.

**Spec:** $ARGUMENTS

Conteúdo:
@$ARGUMENTS

Procedimento:
1. Identifique todos os AC do spec.
2. Para cada AC, crie um teste em `tests/unit/test_<slug>.py` cujo nome ou docstring referencia `AC-N`.
3. Use `pytest-asyncio` + `aioresponses` pra mock HTTP.
4. Cada teste deve falhar com `NotImplementedError` ou `AssertionError` (não `ImportError`).
5. NÃO edite `src/`. Stubs em `src/` já levantam `NotImplementedError`; seus testes forçam o comportamento.
6. Rode `uv run pytest -q tests/unit/test_<slug>.py` no final pra confirmar RED.
7. Imprima o sumário: N testes escritos, todos RED.

Depois do seu retorno, o primary delega pro `test-first-guard` que valida CONTINUE / BLOCKED-*.
