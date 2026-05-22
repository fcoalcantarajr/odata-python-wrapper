---
agent: spec-author
subtask: true
description: Cria novo spec em `specs/NNN-<slug>.md` (N = próximo número livre). Argumento: slug curto kebab-case.
---

Crie um novo spec SDD em `specs/`.

**Slug solicitado:** $ARGUMENTS

Procedimento:
1. Liste `specs/` para encontrar o próximo número livre (NNN).
2. Copie a estrutura de `specs/000-TEMPLATE.md`.
3. Preencha header, user story, use cases, AC Gherkin absoluto, NFRs, INVEST self-score, out-of-scope, test plan, DoD.
4. Salve como `specs/NNN-$ARGUMENTS.md`.
5. Status inicial: DRAFT.
6. Imprima o caminho final + INVEST self-score.

NÃO escreva código nem teste. Só spec.