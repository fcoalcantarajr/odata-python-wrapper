---
name: notion-sync-patterns
description: Quando push vs pull, mapping `specs/NNN.md` -> page Notion (via header HTML), conflict resolution (disk wins por padrão), idempotência via hash sha256, rate limits do Notion MCP. Use em qualquer `/notion-sync` ou hook automático pós-commit.
---

# Notion sync patterns

Usado por `notion-curator` (único com MCP write em `notion`, HR-22).

## When push

- Automático após `/commit` (primary delega via `[NOTION_PUSH_REQUEST]`).
- Manual: `/notion-sync push <path>?`.

## When pull

- Sempre manual: `/notion-sync pull <path>?`.
- Quando humano editou page no Notion UI e quer trazer pro disco.

## Mapping (disk ↔ Notion)

| Disk path                | Notion page                  |
| ------------------------ | ---------------------------- |
| `specs/000-TEMPLATE.md`  | page "Specs / 000-TEMPLATE"  |
| `specs/NNN-*.md`         | page "Specs / NNN-<slug>"    |
| `docs/decisions.md`      | page "ADRs" (full mirror)    |
| `docs/architecture.md`   | page "Architecture"          |
| `AGENTS.md`              | page "AGENTS.md (live)"      |

## Header HTML (no topo do arquivo md)

```
\<!-- notion-page-id: 0123abcd-ef45-6789-abcd-ef0123456789 --\>
\<!-- last-sync-hash: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 --\>
# SPEC-001: ...
```

Notion-curator lê/escreve esses dois headers automaticamente. Eles NÃO contam pro hash do conteúdo.

## Conflict resolution

1. Calcula `disk_hash = sha256(content_without_headers)`.
2. Calcula `notion_hash = sha256(notion_fetch(page_id))`.
3. Decisão:
   - `disk_hash == last_sync_hash and notion_hash == last_sync_hash` → **noop**.
   - `disk_hash != last_sync_hash and notion_hash == last_sync_hash` → **push** (disco mudou).
   - `disk_hash == last_sync_hash and notion_hash != last_sync_hash` → **pull** (Notion mudou).
   - Ambos != → **[NOTION_CONFLICT]**, aborta. Humano roda com `--prefer=disk` ou `--prefer=notion`.
4. Após sucesso, atualiza `last-sync-hash` no header HTML.

## Rate limits

- Notion MCP: ~3 RPS sustentado. Cliente self-throttle em 5 RPS máximo, sleep 200ms entre calls.
- Em 429 do Notion, espera Retry-After e re-tenta uma vez. Mais que isso → `[ESCALATION]`.

## Idempotência

- Hash sha256 garante que push sem mudança é noop.
- `notion-page-id` no header garante que push não cria page duplicada.
- Se header faltar no md, push CRIA page nova e escreve o id de volta no header.