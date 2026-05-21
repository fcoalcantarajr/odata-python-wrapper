---
agent: spec-author
subtask: true
description: Valida um spec contra INVEST + Gherkin absoluto. Retorna APPROVED / ADJUSTMENTS / REQ_BLOCKED.
---

Valide o spec abaixo contra os critérios SDD do projeto.

**Spec:** $ARGUMENTS

Conteúdo do spec:
@$ARGUMENTS

Verifique:
1. Header completo (id, slug, status, created, owner).
2. User Story no formato "As a / I want / So that".
3. ≥ 5 AC Gherkin com Then observável (status, igualdade, exceção nomeada).
4. NFRs presentes (performance, security, observability).
5. INVEST self-score ≥ 8/10 com justificativa por letra.
6. Out-of-scope listado.
7. Test plan com pelo menos um teste por AC.
8. DoD presente.

Retorne **uma** das três strings exatas:
- `APPROVED`
- `ADJUSTMENTS\n<lista de patches sugeridos>`
- `REQ_BLOCKED\n<perguntas que o humano precisa responder>`
