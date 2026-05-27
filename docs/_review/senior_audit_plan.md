# Senior Audit Implementation Plan — Triaged

**Date**: 2026-05-27
**Author**: Momus (planning and QA specialist)
**Source**: `docs/_review/senior_audit_findings.md` — 18 findings (SR-001 through SR-018)
**Status**: SR-001 already fixed (commit bd996e2); remaining 17 findings grouped into 10 specs

---

## Overview

18 findings across 8 buckets, triaged into 10 implementation specs.
SR-001 (SCATHING — `iter_pages` session-None guard) is already fixed.
The remaining 17 findings are grouped by dependency and similarity for parallel execution.

| Priority | Findings | Specs | Worst Severity | Total Effort |
|----------|----------|-------|----------------|-------------|
| **P0** | SR-003, SR-004 | 2 specs | SCATHING | Short + Medium |
| **P1** | SR-005, SR-006, SR-007, SR-011 | 4 specs | SEVERE | 3× Short + Medium |
| **P2** | SR-002, SR-012, SR-013, SR-010, SR-014, SR-018 | 3 specs | MEDIUM | 2× Quick + 2× Short + Medium |
| **P3** | SR-008, SR-009, SR-015, SR-016, SR-017 | 1 spec | TRIVIAL | Quick ×5 |

---

## Dependency Graph

```
SR-001 (FIXED — no deps)
  │
  └── SR-015 (trivial — test xfail → remove xfail, now passes) ──┐
                                                                  │
SR-003 (Retry-After) ── standalone ──────────────────────────────┤
SR-004 (HR-13 dedup) ── standalone ──────────────────────────────┤
SR-005 (integration) ── standalone (new infra) ──────────────────┤
SR-006 (Hypothesis) ── standalone (new tests) ───────────────────┤
SR-007 (mock fixture) ── standalone ─────────────────────────────┤  ALL
SR-011 (timeout) ── standalone ──────────────────────────────────┤  PARALLEL
SR-002+SR-008+SR-009+SR-012 (code cleanup) ── standalone ───────┤
SR-013 (error coverage) ── standalone (pure test addition) ──────┤
SR-010+SR-014+SR-018 (docs cleanup) ── standalone ───────────────┤
SR-015+SR-016+SR-017 (trivial) ── SR-001 done → SR-015 is free ─┘
```

**Key insight**: All 10 specs are *fully parallelizable*. None have hard dependencies on each other. SR-015 logically depends on SR-001 (already fixed), so that dependency is resolved.

---

## Spec-by-Spec Breakdown

### Spec 1: SR-003 — Retry-After on 429
- **Priority**: P0 | **Severity**: SEVERE | **Effort**: Medium (< 3h)
- **Bucket**: B3 (Retry/Backoff Sanity)
- **What**: `retry.py` ignores `Retry-After` header from 429 responses. Custom wait function needed.
- **Changes**: `exceptions.py` (add `retry_after` attr to `RateLimitError`), `_http.py` (pass `retry_after`), `retry.py` (custom wait function)
- **Tests**: New `tests/unit/test_sr_003_retry_after.py`
- **Parallelizable**: Yes — no shared files with other specs

### Spec 2: SR-004 — HR-13 Validation Dedup
- **Priority**: P0 | **Severity**: SCATHING | **Effort**: Short (< 1h)
- **Bucket**: B4 (OData Domain Truth)
- **What**: HR-13 validation exists in 3 places (`_apply.py:175`, `_builder.py:78`, `_builder.py:137`). Extract shared `_check_snapshot_groupby()` function.
- **Changes**: New private module or function in `query/`, refactor `_apply.py` + `_builder.py`
- **Tests**: Existing tests cover HR-13; update to verify shared function directly
- **Parallelizable**: Yes — `query/` module only

### Spec 3: SR-007 — mock_http Fixture Refactor
- **Priority**: P1 | **Severity**: SEVERE | **Effort**: Short (< 1h)
- **Bucket**: B6 (Test Rigor)
- **What**: `tests/conftest.py:38-55` monkey-patches `aioresponses._matches` internals. Refactor to register catch-all last.
- **Changes**: `tests/conftest.py` only
- **Tests**: All existing tests that use `mock_http` will verify the refactored fixture
- **Parallelizable**: Yes — test-only change

### Spec 4: SR-005 — Integration Test Infrastructure
- **Priority**: P1 | **Severity**: SEVERE | **Effort**: Medium (< 3h)
- **Bucket**: B5 (Docs vs Reality)
- **What**: Cookbook claims "tested against real ADO" but no integration tests exist. Create `tests/integration/` directory with one smoke test, gated behind `@pytest.mark.integration`.
- **Changes**: New `tests/integration/` directory, `tests/conftest.py` (marker skip logic), cookbook disclaimer update
- **Tests**: One integration smoke test (skipped by default in CI)
- **Parallelizable**: Yes — new directory, no source file changes

### Spec 5: SR-006 — Hypothesis Property-Based Tests
- **Priority**: P1 | **Severity**: SEVERE | **Effort**: Medium (< 3h)
- **Bucket**: B6 (Test Rigor)
- **What**: Hypothesis is installed but never used. Add `@given` tests for serialize order, Filter roundtrip, entity validation, URL encoding, batch parsing.
- **Changes**: `tests/unit/test_sr_006_hypothesis.py` (new file)
- **Tests**: At least 3 property-based tests exercising pure functions
- **Parallelizable**: Yes — test-only change

### Spec 6: SR-011 — Client Timeout Configuration
- **Priority**: P1 | **Severity**: SEVERE | **Effort**: Short (< 1h)
- **Bucket**: B1 (Async Correctness)
- **What**: `client.py` creates `ClientSession` without `timeout=` parameter. Add optional `ClientTimeout` parameter to `__init__()`.
- **Changes**: `src/ado_odata_async/client.py` only
- **Tests**: New test verifying timeout is passed to ClientSession, and default fallback behavior
- **Parallelizable**: Yes — `client.py` only

### Spec 7: SR-002 + SR-008 + SR-009 + SR-012 — Code Cleanup
- **Priority**: P2/P3 | **Severity**: MEDIUM | **Effort**: Quick (< 15min each)
- **Buckets**: B2, B4
- **Contents**:
  - **SR-002**: Remove redundant `field_validator` on `WorkItemType` (leave `Literal` type)
  - **SR-008**: Fix `__setattr__` to catch `FrozenInstanceError` specifically, not `ValidationError`
  - **SR-009**: Document or remove double-filter in `pagination.py:50-52`
  - **SR-012**: Change `query.get("$expand")` to `filtered.get("$expand")` in `_serialize.py:58`
- **Changes**: 4 files, minimal edits
- **Tests**: Existing tests verify all behaviors; no new tests required
- **Parallelizable**: Yes — 4 independent changes in one spec

### Spec 8: SR-013 — Error Path Coverage
- **Priority**: P2 | **Severity**: MEDIUM | **Effort**: Medium (< 3h)
- **Bucket**: B6 (Test Rigor)
- **What**: Add tests for uncovered error-path lines in `_http.py` (75%), `client.py` (84%), `_builder.py` (70%)
- **Changes**: `tests/unit/test_sr_013_error_coverage.py` (new file)
- **Tests**: At least 5 tests covering the specific missing lines
- **Parallelizable**: Yes — test-only change

### Spec 9: SR-010 + SR-014 + SR-018 — Docs Cleanup
- **Priority**: P2/P3 | **Severity**: MEDIUM | **Effort**: Short (< 1h)
- **Buckets**: B5, B8
- **Contents**:
  - **SR-010**: Remove dead `Filter` import from `getting-started.md`
  - **SR-014**: Update 37 stale RED-phase docstrings in test files
  - **SR-018**: Add machine-verifiable AC to Spec 012 via a doc-check test
- **Changes**: Multiple doc files + new test file
- **Parallelizable**: Internally parallel; no source code changes

### Spec 10: SR-015 + SR-016 + SR-017 — Trivial Fixes
- **Priority**: P3 | **Severity**: TRIVIAL | **Effort**: Quick (< 15min each)
- **Buckets**: B6, B3, B7
- **Contents**:
  - **SR-015**: Remove `xfail` (if present) from SR-001 test — now passes with SR-001 fix
  - **SR-016**: Simplify `_stop()` logic in `retry.py` — remove confusing `rate_limit_max` variable
  - **SR-017**: Add `__all__` to entity submodules (`_workitem.py`, `_board.py`, etc.)
- **Changes**: 6+ files, minimal edits each
- **Tests**: Existing tests cover behaviors; SR-015 test should now pass

---

## Parallelization Map

```
WAVE 1 (all at once, zero conflicts):
  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
  │ SR-003 │  │ SR-004 │  │ SR-007 │  │ SR-005 │  │ SR-006 │
  │ retry  │  │ hr13   │  │ mock   │  │ integ  │  │ hypoth │
  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘
  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
  │ SR-011 │  │cleanup │  │ SR-013 │  │docs    │  │trivial │
  │timeout │  │(4 in 1)│  │coverage│  │cleanup │  │(5 in 1)│
  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘

File conflict map:
  - SR-003: exceptions.py, _http.py, retry.py  ← UNIQUE
  - SR-004: _apply.py, _builder.py              ← UNIQUE
  - SR-007: tests/conftest.py                   ← UNIQUE
  - SR-005: tests/conftest.py                   ← CONFLICT with SR-007 (same file!)
  - SR-011: client.py                           ← UNIQUE
  - SR-002: _workitem.py                        ← UNIQUE
  - SR-008: entities/_base.py                   ← UNIQUE
  - SR-009: pagination.py                       ← UNIQUE
  - SR-012: _serialize.py                       ← UNIQUE
  - SR-013: test-only (new file)                ← UNIQUE
  - SR-010: docs/getting-started.md             ← UNIQUE
  - SR-014: test/ files only (docstrings)       ← UNIQUE
  - SR-015: test_sr_001_pagination_session.py   ← UNIQUE
  - SR-016: retry.py                            ← CONFLICT with SR-003!
  - SR-017: entities/*.py (submodules)          ← UNIQUE
```

**Conflict resolution**:
- **SR-005 + SR-007** both modify `tests/conftest.py` → merge or sequence: SR-007 first, then SR-005
- **SR-003 + SR-016** both modify `retry.py` → SR-003 (medium, P0) handles `retry.py` comprehensively; fold SR-016 into SR-003's changes

---

## Execution Order Recommendation

```
Phase 1 (P0 — must fix):
  ┌─────────────────────────────────────────────┐
  │ Track 1: SR-003 (includes SR-016)  retry.py │
  │ Track 2: SR-004                   query/    │  ← fully parallel
  └─────────────────────────────────────────────┘

Phase 2 (P1 — should fix):
  ┌─────────────────────────────────────────────┐
  │ Track 3: SR-007 → then SR-005  conftest.py  │  ← sequential (same file)
  │ Track 4: SR-006                  tests/     │
  │ Track 5: SR-011                  client.py  │  ← fully parallel except 3+5
  └─────────────────────────────────────────────┘

Phase 3 (P2/P3 — fix after):
  ┌─────────────────────────────────────────────┐
  │ Track 6: SR-002+008+009+012    code/        │
  │ Track 7: SR-013                 tests/      │
  │ Track 8: SR-010+014+018         docs+tests/ │  ← fully parallel
  │ Track 9: SR-015+017             code+tests/ │
  └─────────────────────────────────────────────┘
```

**Phases are sequential**: Phase 1 → Phase 2 → Phase 3.
**Tracks within a phase** are parallel.
**Total wall-clock time**: ~1 day of parallel implementation.

---

## Coverage Impact

| After spec | Expected coverage | Files that improve |
|------------|------------------|--------------------|
| SR-003     | 89% → 90%        | retry.py (97%→100%), _http.py (75%→77%) |
| SR-004     | 89% → 90%        | _builder.py (70%→78%) |
| SR-007     | No change (test) | — |
| SR-005     | No change (test) | — |
| SR-006     | No change (test) | — |
| SR-011     | ~89%             | client.py (84%→86%) |
| SR-002     | ~89%             | _workitem.py (83%→87%) — fewer lines |
| SR-013     | 89% → 90%+       | _http.py (75%→90%), client.py (84%→90%), _builder.py (70%→85%) |
| SR-008/009/012/016/017 | ~89% | Marginal improvements |

**Target after all specs**: 90%+ line coverage, error-path coverage > 85%.

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| SR-003 custom wait function breaks retry | Low | High | Unit test with mock 429 returning specific Retry-After |
| SR-004 refactor changes HR-13 behavior | Low | High | Same tests must pass before/after |
| SR-005 integration test leaks credentials | Low | Medium | `getpass` prompt or env-var-only, never hardcoded |
| SR-007 fixture refactor breaks existing tests | Medium | Medium | All 129 tests must still pass |
| SR-011 timeout breaks existing client usage | Low | Low | Backward-compatible default |
| SR-013 tests become flaky | Low | Low | Mock-based, no real I/O |
