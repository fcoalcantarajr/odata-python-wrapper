---
agent: git-keeper
subtask: true
description: Sincroniza com remoto via `git pull --rebase --autostash` + `git push`. Aborta com [ESCALATION] em conflict markers.
---

Sincronize com o remoto.

Procedimento:
1. `git fetch origin`.
2. `git pull --rebase --autostash`.
3. Se aparecer conflict marker (`<<<<<<<`, `=======`, `>>>>>>>`) em qualquer arquivo → `[ESCALATION] git conflict markers`. Pare.
4. Rode `uv run pytest -q` após rebase pra confirmar GREEN.
5. `git push`.
6. Imprima o hash do HEAD final.
