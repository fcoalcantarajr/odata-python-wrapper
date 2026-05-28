<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# AS-103 — Remove phantom runtime dependencies python-dateutil and python-dotenv

- id: AS-103
- slug: phantom-deps
- status: APPROVED
- created: 2026-05-28
- owner: sisyphus
- findings-addressed: AS-103

## User Story

As a library consumer minimizing dependency footprint,
I want only truly needed runtime dependencies in pyproject.toml,
so that install times and attack surface are not inflated by unused packages.

## Use Cases

- UC1: `python-dateutil>=2.9,<3` removed from `[project] dependencies`
- UC2: `python-dotenv>=1.2.2` removed from `[project] dependencies`
- UC3: `types-python-dateutil` remains in `[dependency-groups.dev]` (for pre-existing type stubs)
- UC4: AGENTS.md STACK section updated to reflect current dependencies
- UC5: `uv sync` succeeds and all tests pass after removal

## Acceptance Criteria (Gherkin absoluto)

### AC-1: python-dateutil removed from runtime deps

```
Given the pyproject.toml [project] dependencies section
When searched for "python-dateutil"
Then no match is found
```

### AC-2: python-dotenv removed from runtime deps

```
Given the pyproject.toml [project] dependencies section
When searched for "python-dotenv"
Then no match is found
```

### AC-3: types-python-dateutil retained in dev deps

```
Given pyproject.toml [dependency-groups.dev]
When searched for "types-python-dateutil"
Then exactly one match is found
```

### AC-4: All tests still pass

```
Given the project with updated dependencies
When uv run pytest -q is executed
Then exit code is 0
```

### AC-5: uv sync succeeds

```
Given the project with updated pyproject.toml
When uv sync is executed
Then exit code is 0
```

### AC-6: AGENTS.md updated

```
Given the AGENTS.md file
When searched for "python-dateutil" or "python-dotenv" in the STACK section
Then neither is found in the STACK pin list
```

## NFRs

- **Zero production behavior change:** No code changes to `src/` — only pyproject.toml and AGENTS.md
- **Dev deps preserved:** types-python-dateutil stays as development dependency (pre-existing type stubs)

## INVEST self-score

- **I**ndependent: 10/10 — no code changes
- **N**egotiable: 9/10 — exact trim list is negotiable
- **V**aluable: 8/10 — reduces install footprint
- **E**stimable: 10/10 — < 3 lines changed
- **S**mall: 10/10 — removes 2 lines
- **T**estable: 10/10 — grep + uv sync + pytest

Média: 9.5/10

## Out of scope

- Removing types-python-dateutil from dev deps (explicitly kept)
- Adding new dependencies
- Auditing other optional dependencies
- Changes to src/ code

## Test plan

- AC-1 → grep pyproject.toml for python-dateutil in [project]
- AC-2 → grep pyproject.toml for python-dotenv in [project]
- AC-3 → grep pyproject.toml for types-python-dateutil in [dependency-groups.dev]
- AC-4 → uv run pytest -q
- AC-5 → uv sync
- AC-6 → grep AGENTS.md for python-dateutil/python-dotenv in STACK section

## DoD

- [ ] AC-1 a AC-6 verdes
- [ ] `uv run pytest -q` exit 0
- [ ] `uv run ruff check .` exit 0
- [ ] `uv run mypy src/` exit 0
- [ ] `bash scripts/audit.sh` exit 0
