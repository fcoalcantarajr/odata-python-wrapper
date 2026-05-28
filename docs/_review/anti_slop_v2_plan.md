# anti_slop_v2_plan.md — Triage & Execution Plan
> Phase 3 output from AI-skeptical self-audit, ado_odata_async

## MONITOR-LOOP CHECK

**Root cause clustering** across 7 findings (AS-101 through AS-107):

| Root Cause | Findings | Count | Action |
|------------|----------|-------|--------|
| Regex bug in validation logic | AS-101 | 1 | Individual spec |
| Domain model over-constraint | AS-102 | 1 | Individual spec |
| Configuration/debt (phantom deps) | AS-103 | 1 | Individual spec |
| Test gap (unit-level) | AS-104 | 1 | Individual spec |
| Test gap (infrastructure-level) | AS-105 | 1| Individual spec (existing AS-005) |
| Documentation quality | AS-106 | 1 | Individual spec (existing AS-010) |
| Doc-code duplication | AS-107 | 1 | Bundle in CLEANUP-2 |

**Verdict: No 3+ findings share a single root cause.** AS-104 and AS-105 share a "test coverage" theme but are structurally different (unit coverage gap vs missing integration infra). Threshold not met. **No META-SPEC required.**

---

## AUDIT-FRAMEWORK CHECK

### 8 OData Gotchas

| # | Gotcha | Classification | Evidence Cited |
|---|--------|---------------|----------------|
| 1 | PAT auth: empty username | **canonical** | MS Learn `use-personal-access-tokens-to-authenticate` — `":" + PAT` header |
| 2 | Query option order | **composite** | MS `odata-supported-features` says "order ignored"; MS `analytics-query-parts` gives a recommended order. v4.0-preview may differ. |
| 3 | URL > 3000 chars → POST batch | **canonical** | MS `odata-query-guidelines` — explicit 3000 char GET limit + batch workaround |
| 4 | Snapshot requires groupby DateSK/DateValue | **canonical** | MS `odata-query-guidelines` — "DO include DateSK/DateValue" |
| 5 | `$expand=Revisions` blocked | **composite** | MS says "DON'T use" (recommendation); project says blocked/400 (verified empirically) |
| 6 | Single-quote escape by doubling | **canonical** | OData v4 spec — standard string literal |
| 7 | ISO 8601 datetime, no `datetime'` prefix | **canonical** | OData v4 spec — v3 syntax dropped |
| 8 | HTTP 203 + text/html = PAT invalid | **composite** | Project-specific empirical discovery |

### 13 Fingerprints F1-F13 (AI-Archaeology)

**Classification: fabricated** — Entirely project-internal classification system. Not an industry standard or external tool. Defined in project audit docs only.

### 22 Hard Rules HR-1 through HR-22

**Classification: fabricated** — Entirely project-specific governance rules defined in `AGENTS.md`. No external standard maps to these.

---

## G0–G6 Gate Cycle (per spec)

Each spec passes through the full gate cycle below. The task's original specification mandates this structure.

### G0 — Anti-sycophancy pre-fix (Oracle)
- Delegate to Oracle: "Answer Q5 + Q6 on the proposed fix. If either fails, shrink scope or REJECT the spec back to triage."
- Q5: Is this fix solving the actual root cause, or polishing a symptom?
- Q6: Is this the SMALLEST fix that GREENs the test, and am I exceeding it?
- If blocked → spec goes back to triage

### G1 — Spec-check (spec-author)
- `/spec-check` → must return APPROVED (≥ 8/10 INVEST, observable ACs)
- **Current status:**
  - AS-005: ✅ APPROVED (patched from ADJUSTMENTS)
  - AS-010: ✅ APPROVED (patched from ADJUSTMENTS)
  - AS-101: ✅ APPROVED
  - AS-102: ✅ APPROVED
  - AS-103: ✅ APPROVED
  - AS-104: ✅ APPROVED
  - AS-CLEANUP-2: ✅ APPROVED

### G2 — Test-first (atlas)
- atlas writes `tests/unit/test_<slug>.py` that FAILS (RED)
- Pins the bug / slop / rule-violation with assertions
- test-first-guard confirms RED before G3

### G3 — Implement (hephaestus)
- hephaestus writes minimum HAND-WRITTEN fix to GREEN
- NO LLM suggestion accepted verbatim
- Changes only `src/` (never `tests/`)

### G4 — Review (oracle + odata-reviewer)
- oracle: async correctness, logic verification
- odata-reviewer: HARD RULES + domain gotchas check
- Both must APPROVE

### G5 — Coverage + pytest
- `uv run pytest -q` 100% pass
- `uv run pytest --cov=ado_odata_async --cov-fail-under=85` GREEN

### G6 — Static gates
- `uv run ruff check .` clean
- `uv run mypy src/` strict clean
- `bash scripts/audit.sh` exit 0

### Commit
- `git-keeper` executes 4-stage gate + Conventional Commit referencing `(AS-NNN)`

---

## Execution Order & Dependencies

### AS-101 (SCATHING-fundamentals) — HIGHEST priority
```
G0 → G1 ✅ → G2 → G3 → G4 → G5 → G6 → git-keeper commit
```
Fix regex in `_apply.py:282`: `r"groupby\(\(([^)]+)\)\)"` → `r"groupby\(\(([^)]+)\)"`
~3 LOC src, ~40 LOC test.

### AS-102 (SEVERE)
```
G0 → G1 ✅ → G2 → G3 → G4 → G5 → G6 → git-keeper commit
```
Change `WorkItemType: Literal[...]` → `str` in `_workitem.py:29`.
~2 LOC src, ~20 LOC test.

### AS-103 + AS-104 (MEDIUM, parallelizable)
```
AS-103: G0 → G1 ✅ → G2 → G3 → G4 → G5 → G6 → git-keeper commit
AS-104: G0 → G1 ✅ → G2 → G3 → G4 → G5 → G6 → git-keeper commit
```
- AS-103: Remove phantom deps from `pyproject.toml`, no src/ changes
- AS-104: Add unit tests for batch POST error paths, test-only

### AS-105/AS-005 (MEDIUM, already implemented)
```
G1 ✅ (retroactive) → G4 → G5 → G6 → git-keeper commit (if needed)
```
Already in commit 18f5da1. Retroactive gate pass-through.

### AS-106/AS-010 (MEDIUM, already implemented in README)
```
G1 ✅ (retroactive) → G4 → G5 → G6 → git-keeper commit
```
README changes per file ownership table (human/librarian, not hephaestus).

### AS-CLEANUP-2 (TRIVIAL bundle)
```
G0 → G1 ✅ → G2 → G3 → G4 → G5 → G6 → git-keeper commit
```
Remove duplicate HR-13 enforcement notes from AGENTS.md (3 lines).

---

## MONITOR-LOOP (ongoing check)

**Root cause clustering** across 7 findings (AS-101 through AS-107):
- AS-101 (regex bug), AS-102 (over-constraint), AS-103 (phantom deps): independent
- AS-104/AS-105 (test gaps): different layers (unit vs integration)
- AS-106 (docs), AS-107 (doc-code duplication): documentation
- **Verdict:** No 3+ findings share a single root cause. No META-SPEC required.
- **Ongoing:** Re-evaluate after every 3rd commit for emergent clusters.

---

## Execution Priority Order

1. **AS-101** (SCATHING-fundamentals) — unblocks ALL snapshot+aggregate queries
2. **AS-102** (SEVERE) — blocks custom process templates
3. **AS-103** (MEDIUM, no src/) — quickest win
4. **AS-CLEANUP-2** (MEDIUM, no src/) — trivial AGENTS.md fix
5. **AS-104** (MEDIUM, test-only) — coverage gap
6. **AS-005** (MEDIUM, already implemented) — retroactive verification
7. **AS-010** (MEDIUM, already implemented) — retroactive verification
