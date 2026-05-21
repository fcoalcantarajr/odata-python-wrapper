---
name: spec-driven-development
description: Como escrever spec SDD com User Story + Gherkin AC absoluto + INVEST self-score. Use quando criar `specs/NNN-*.md`, quando validar com `/spec-check`, ou quando avaliar se uma feature é ambigua demais pra virar código.
---

# Spec-driven development

## When to use

- Antes de qualquer código: feature nova precisa de spec.
- Em `/spec` (criar) ou `/spec-check` (validar).
- Quando um requisito chegou vago demais ("melhorar performance") e precisa virar Gherkin absoluto.

## Estrutura canônica do spec

```
# SPEC-NNN: \<Título curto\>
- id: SPEC-NNN
- slug: \<kebab-case\>
- status: DRAFT | APPROVED | IMPLEMENTED
- created: YYYY-MM-DD
- owner: \<user\>
## User Story
As a \<persona\>, I want \<capacidade\>, so that \<valor\>.
## Use Cases
- UC1: ...
- UC2: ...
## Acceptance Criteria (Gherkin)
### AC-1: \<título\>
Given \<pre-condição observável\>
When \<ação\>
Then \<pós-condição observável — status code, igualdade, exceção nomeada\>
## NFRs
- Performance: ...
- Security: ...
- Observability: ...
## INVEST self-score
- I (Independent): 9/10 — ...
- N (Negotiable):  8/10 — ...
- V (Valuable):    10/10 — ...
- E (Estimable):   9/10 — ...
- S (Small):       8/10 — ...
- T (Testable):    10/10 — ...
Total média: 9.0/10
## Out-of-scope
- ...
## Test plan
- AC-1 → tests/unit/test_\<slug\>.py::test_\<...\>
- ...
## DoD
- [ ] Todos AC GREEN
- [ ] Coverage ≥ 85%
- [ ] HARD RULES respeitadas
- [ ] Conventional Commit
```

## Regras pra Gherkin absoluto

**RUIM** (observabilidade fraca):
- Then "o sistema funciona corretamente"
- Then "a performance é aceitável"
- Then "o código é limpo"

**BOM** (observável):
- Then a resposta HTTP é `200` e o corpo contém `{"count": 3}`
- Then `client._session` é o mesmo objeto antes e depois da segunda chamada
- Then a chamada levanta `AuthenticationError` com mensagem contendo `"203"`

## INVEST scoring (cada letra 1-10)

- **I**ndependent: pode entregar sem outras specs.
- **N**egotiable: detalhes podem mudar sem virar outra spec.
- **V**aluable: humano consegue dizer o valor sem "depois explico".
- **E**stimable: dev consegue prever esforço.
- **S**mall: cabe em uma sessão de impl (≤ 1 dia equivalente).
- **T**estable: tem assertion clara em código.

Spec com média < 8 → reescreve. Média < 6 → `REQ_BLOCKED`.
