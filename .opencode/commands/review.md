---
agent: oracle
subtask: true
description: Review async correctness (oracle do omo). Em seguida, o primary delega pro `odata-reviewer` pra checar HARD RULES + gotchas domínio.
---

Review da implementação atual.

Fase 1 (você, oracle):
- Async correctness: sem `asyncio.run` aninhado, sem `loop.run_until_complete` em libcode, `async with` em ClientSession, cancel propagation correto, sem race em fixtures.
- Type safety: nada de `Any` fora de boundary, generics corretos.
- Estrutura: separation of concerns OK, sem duplicação óbvia.

Fase 2 (delegada pelo primary):
- O primary chama `odata-reviewer` no segundo passe pra checar HR-7..HR-22 + 8 gotchas.

Seu output:
```
APPROVED
```
ou
```
CHANGES_REQUESTED
- \<path:linha\> — \<descrição\>
```