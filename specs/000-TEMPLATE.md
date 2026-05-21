<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# SPEC-NNN: <Título curto e descritivo>

- id: SPEC-NNN
- slug: <kebab-case>
- status: DRAFT
- created: YYYY-MM-DD
- owner: <@user>

## User Story

As a <persona>, I want <capacidade>, so that <valor>.

## Use Cases

- UC1: ...
- UC2: ...
- UC3: ...

## Acceptance Criteria (Gherkin absoluto)

Cada AC tem Then **observável** (status code, igualdade, exceção nomeada, identidade de objeto).

### AC-1: <título curto>

```
Given \<pre-condição observável\>
When \<ação\>
Then \<pós-condição observável\>
```

### AC-2: <título curto>

```
Given ...
When ...
Then ...
```

## NFRs

- **Performance:** <e.g. p99 < 500ms em mock>
- **Security:** <e.g. PAT nunca aparece em log; mask em `auth.mask_pat`>
- **Observability:** <e.g. log estruturado em DEBUG mostra request id e v4.0-preview>

## INVEST self-score

- **I**ndependent: N/10 — <justificativa>
- **N**egotiable:  N/10 — <justificativa>
- **V**aluable:    N/10 — <justificativa>
- **E**stimable:   N/10 — <justificativa>
- **S**mall:       N/10 — <justificativa>
- **T**estable:    N/10 — <justificativa>

Média: N/10 (mínimo 8 pra `APPROVED`)

## Out-of-scope

- ...
- ...

## Test plan

- AC-1 → `tests/unit/test_<slug>.py::test_ac1_<...>`
- AC-2 → `tests/unit/test_<slug>.py::test_ac2_<...>`

## DoD

- [ ] Todos AC verdes em `uv run pytest -q tests/unit/test_<slug>.py`
- [ ] Coverage do módulo tocado ≥ 85%
- [ ] `ruff check .`, `mypy src/` exit 0
- [ ] `bash scripts/audit.sh` exit 0
- [ ] HARD RULES respeitadas (lista as relevantes)
- [ ] Conventional Commit emitido por `git-keeper` referenciando `(SPEC-NNN)`
