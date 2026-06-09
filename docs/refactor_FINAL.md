# Refactor Final — Audit Remediation + Doc-as-Contract

Completed: 2026-06-09

## Summary

Comprehensive audit remediation and documentation-as-contract rewrite for ado-odata-async v0.1.0. Public API frozen (byte-identical export names and signatures). Internal refactor only.

## Findings Closed

### F1: ruff/pyproject — RUF200 on license-files
- **Root cause**: ruff 0.6.9 doesn't support PEP 639 (`license-files` in pyproject.toml)
- **Fix**: Upgraded ruff from 0.6.9 → 0.15.16 in pyproject.toml and lockfile
- **Additional**: Fixed 5 new lint errors surfaced by ruff 0.15.16 (RUF022, UP047, RUF043 x3)
- **Verification**: `ruff check .` exits 0

### F2: Broken doc links
- **Root cause**: HANDOFF.md referenced `AGENTS.md` with wrong relative path
- **Fix**: Changed `[AGENTS.md](AGENTS.md)` → `[AGENTS.md](../AGENTS.md)` in docs/HANDOFF.md
- **Note**: docs/_review/ has 7 additional broken links (internal scratch, proposed for gitignore)
- **Verification**: HANDOFF.md link resolves correctly

### F3: Undocumented public API
- **Root cause**: BaselineResult, FlowTimeResult, PlanHistoryResult + 3 compute functions not documented in README
- **Fix**: Added "Flow Metrics & Delivery Analytics" section to README with 6 subsections, each with runnable usage examples. Portuguese section updated equivalently.
- **Verification**: README links resolve, examples use correct import paths

### F4: Missing docstrings (PEP 257)
- **Root cause**: 11 functions/classes had no docstrings
- **Fix**: Added Google Style docstrings to all 11 targets
- **Verification**: All docstrings describe actual behavior, not aspirations

### F5: Spec status DRAFT → IMPLEMENTED
- **Root cause**: Specs 013-017 had `status: DRAFT` despite full implementation
- **Fix**: Updated status to IMPLEMENTED in all 5 spec files
- **Verification**: Each spec has passing tests (46 total), 93-100% coverage, clean ruff/mypy

## Gate Results

```
=== Code Gates ===
ruff check ... ok
mypy --strict ... ok
pytest ... ok (252 passed, 13 skipped)
coverage ... ok (97.83%)
audit.sh ... ok

=== Doc Gates ===
public API signature ... ok (unchanged)
HANDOFF.md -> AGENTS.md ... ok

AUDIT PASSED
```

## Junior-User Doc-Only Run

Successfully pulled real Azure DevOps Analytics metrics using ONLY docs:
- Basic query: 24,275 completed items
- Plan History: created_date=2023-12-21, on_time_rate=33.3%
- Flow Times: 50 state transitions for WorkItemId 2309
- Baseline Metrics: 4 target date changes, replanned=True

## Frozen Invariants Preserved

- ODATA_VERSION = "v4.0-preview" (single source of truth)
- Single ClientSession per client (HR-7)
- BasicAuth("", PAT) — empty username (HR-8)
- Query serialization order preserved (HR-9)
- expand=Revisions blocked → use WorkItemRevisions (HR-14)
- Public export names + signatures: byte-identical vs baseline
