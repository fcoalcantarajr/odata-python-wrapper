<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# SPEC-012: Documentation + ADRs — public docs + architecture + cookbook

- id: SPEC-012
- slug: docs-adrs
- status: DRAFT
- created: 2026-05-22
- owner: @opencode

## User Story

As a new developer joining the project, I want complete documentation (architecture.md, cookbook.md, upgraded README, and all ADRs committed) so that I can understand the system without reading every source file.

## Use Cases

- UC1: architecture.md with full system diagram and ClientSession lifecycle.
- UC2: cookbook.md with 10 worked examples.
- UC3: README.md upgraded from skeleton to full usage doc.
- UC4: All ADRs (001-008) committed.

## Acceptance Criteria (Gherkin absoluto)

### AC-1: architecture.md exists and covers all layers

```
Given docs/architecture.md
When lido
Then contém seções para Auth, HTTP transport, Client, Retry, Query, Pagination, Metadata, Entities, Exceptions
  And contém fluxo de chamada
  And contém decisões chave (HR-7, HR-8, HR-19)
```

### AC-2: cookbook.md with 10 examples

```
Given docs/cookbook.md
Then contém ao menos 10 exemplos
  And exemplos incluem WorkItems query, $apply, $batch, pagination, retry, error handling
```

### AC-3: README.md upgraded

```
Given README.md
Then contém setup, usage example, development guide, link to AGENTS.md
  And contém pelo menos um exemplo funcional de AdoODataClient
```

### AC-4: All ADRs committed in docs/decisions.md

```
Given docs/decisions.md
Then contém ADR-001 até ADR-008 no formato [INSTITUTED]
```

## INVEST self-score

Média: 9.0/10

## Test plan

- AC-1 → check architecture.md sections
- AC-2 → count code examples in cookbook.md
- AC-3 → README.md has usage example
- AC-4 → grep ADR-001..ADR-008 in decisions.md

## DoD

- [ ] architecture.md, cookbook.md, README.md atualizados
- [ ] `ruff check .`, `mypy src/` exit 0
- [ ] `bash scripts/audit.sh` exit 0
- [ ] Conventional Commit `(SPEC-012)`
