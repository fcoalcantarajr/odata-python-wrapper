<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# Backlog

Status codes: `DRAFT` (rascunho), `APPROVED` (passou no `/spec-check`), `IMPLEMENTED` (commit + GREEN), `DEFERRED` (não agora).

## Próximas 12 specs

| # | Slug | Foco | HARD RULES tocadas | Status |
| --- | --- | --- | --- | --- |
| SPEC-001 | http-skeleton | Single session + v4.0-preview + BasicAuth empty user | HR-7, HR-8, HR-19, HR-20 | DRAFT |
| SPEC-002 | auth-error-mapping | 401, 203+text/html → AuthenticationError; mask PAT em logs | HR-15, HR-16 | DRAFT |
| SPEC-003 | retry-tenacity | retry só em TransientError/RateLimitError; expo+jitter; cap | HR-15 | DRAFT |
| SPEC-004 | pagination | AsyncIterator over `$skip`; respeita `@odata.nextLink` se aparecer | — | DRAFT |
| SPEC-005 | filter-dsl | Builder de `$filter` (eq, and, or, not, contains); escape de aspa simples | HR-12 | DRAFT |
| SPEC-006 | apply-dsl | Builder de `$apply` (filter, groupby, aggregate) para snapshots | HR-13 | DRAFT |
| SPEC-007 | serialization-order | Serializer canônico de query options (ordem fixa) | HR-9 | DRAFT |
| SPEC-008 | batch-post | URL > 3000 chars → `POST $batch` multipart/mixed | HR-10 | DRAFT |
| SPEC-009 | workitem-entity | `WorkItem` Pydantic frozen+strict; fetch por id; teste de schema drift | HR-4 | DRAFT |
| SPEC-010 | remaining-entities | 12 entities restantes (WorkItemRevisions, Iteration, Project, Team, WorkItemBoardSnapshot, etc.) | HR-4, HR-13, HR-14 | DRAFT |
| SPEC-011 | fluent-api | Query builder fluente em cima das DSLs anteriores | — | DRAFT |
| SPEC-012 | docs-adrs | Documentação pública + autodoc (mkdocs) + ADRs (ADR-001..ADR-008) commitados | — | DRAFT |

## Critérios de priorização

1. Bloqueia outras specs? → sobe (SPEC-001, SPEC-007 fazem isso).
2. Risco de retrabalho se ficar pra depois? → sobe.
3. Valor isolado pro usuário final? → sobe.

## Defer

- Streaming responses (não-paginação): adiar até caso de uso real.
- Cliente CLI (separar em outro repo se virar relevante).