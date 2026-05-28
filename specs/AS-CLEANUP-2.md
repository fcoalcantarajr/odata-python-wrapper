<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# AS-CLEANUP-2 — Trivial fixes bundle

- id: AS-CLEANUP-2
- slug: cleanup-bundle-trivial
- status: APPROVED
- created: 2026-05-28
- owner: sisyphus
- findings-addressed: AS-107
- supersedes: AS-CLEANUP-trivial-fixes.md (abandoned — switching from multi-finding bundle to one-finding-per-spec)

## User Story

As a maintainer enforcing documentation hygiene,
I want trivial findings fixed collectively to reduce administrative overhead,
so that attention is focused on substantive improvements.

---

## Finding AS-107: AGENTS.md HR-13 entry duplicates code docstring

### User Story

As a developer reading AGENTS.md,
I want each HR rule entry to be concise and reference the code as single source of truth,
so that governance documentation does not drift from code behavior.

### Acceptance Criteria

#### AC-107-1: HR-13 enforcement notes block is removed from AGENTS.md

```
Given the file AGENTS.md
When the file is searched for the literal string "HR-13"
Then exactly 1 line matches
  And that matching line is the inline rule under "## HARD RULES"
```

Note: `grep -c 'HR-13' AGENTS.md` must return `1`, and the matching line must be the rule entry `- **HR-13** ...`, not the old enforcement notes block.

### Fix

Remove the "Audit.sh Enforcement Notes" block for HR-13 (current lines 77-79). The inline rule at line 47 is the sole remaining source for HR-13 in AGENTS.md. No condensation — just deletion of the duplicate.

## NFRs

- **Single source of truth:** The detailed enforcement rationale for HR-13 exists only in the docstring of `_check_snapshot_groupby()`. AGENTS.md references the rule but does not duplicate the explanation.
- **Minimal diff:** The change to AGENTS.md does not exceed 5 lines (removing the enforcement notes block).

## Out of scope

- Changes to other HR rules that also have enforcement notes descriptions
- Changes to `scripts/audit.sh`
- Changes to `src/` or `tests/`
- Consolidating the remaining inline HARD RULES formatting

## Test plan

- AC-107-1 → `grep -c 'HR-13' AGENTS.md` → must return 1; verify the line starts with `- **HR-13**`

## INVEST self-score (bundled)

- **I**ndependent: 10/10 — documentation only
- **N**egotiable: 10/10 — exact wording negotiable
- **V**aluable: 7/10 — prevents doc-code drift
- **E**stimable: 10/10 — < 3 lines
- **S**mall: 10/10 — trivial change
- **T**estable: 8/10 — grep-able; AC-1 verifies exact match count, not just presence

Média: 9.2/10

## DoD

- [ ] AC-107-1 verde (grep -c 'HR-13' AGENTS.md == 1)
- [ ] `uv run pytest -q` exit 0 (no code changes)
- [ ] `uv run ruff check .` exit 0
- [ ] `bash scripts/audit.sh` exit 0
