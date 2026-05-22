---
agent: retrospector
subtask: true
description: Retro a cada 3-4 specs. Append `[CANDIDATE]` em `docs/decisions.md` + entries em `.opencode/skills/anti-patterns/SKILL.md`. NUNCA gradua candidate -> instituted.
---

Retrospectiva do período.

**Range (opcional):** $ARGUMENTS  (default: `HEAD~10..HEAD`)

Procedimento:
1. `git log --oneline <range>` — liste commits.
2. Identifique padrões repetidos (3+ ocorrências do mesmo tipo de retrabalho).
3. Append em `docs/decisions.md` como `[CANDIDATE] ADR-XXX`.
4. Se anti-pattern novo emergiu, append em `.opencode/skills/anti-patterns/SKILL.md` como `AP-NNN`.
5. Imprima o resumo: N commits analisados, M candidates propostos, K anti-patterns novos.

NÃO gradue `[CANDIDATE]` para `[INSTITUTED]`. Só humano.