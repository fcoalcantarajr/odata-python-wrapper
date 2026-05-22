---
agent: notion-curator
subtask: true
description: Sincroniza disco <-> Notion via Notion MCP. Subcomandos push | pull | status. Conflict resolution: disk wins por padrão, conflict abortado pede confirmação humana.
---

Sincronize estado disco <-> Notion.

**Argumento:** $ARGUMENTS  (formato: `push|pull|status [path] [--prefer=disk|notion]`)

Procedimento:
1. Parse o argumento (subcomando + path opcional + flag).
2. Para cada arquivo no mapping (specs/, docs/, AGENTS.md):
   - Leia o header HTML `<!-- notion-page-id: ... -->` e `<!-- last-sync-hash: sha256:... -->`.
   - Calcule hash atual do disco.
   - Fetch hash da page Notion via MCP.
   - Compare:
     - Ambos divergiram → `[NOTION_CONFLICT] <path>` (aborta sem flag explicita).
     - Só disco mudou → push.
     - Só Notion mudou → pull.
     - Nenhum mudou → noop.
3. **status**: apenas reporta diff, não aplica nada.
4. **push**: aplica disk -> Notion via MCP `update-page`.
5. **pull**: aplica Notion -> disk; edita o arquivo local mantendo o header HTML.
6. Atualiza `last-sync-hash` após sucesso.
7. Rate limit: 5 RPS máximo (sleep 200ms entre calls MCP).

Imprima o sumário: N pushed, M pulled, K conflicts, L noop.