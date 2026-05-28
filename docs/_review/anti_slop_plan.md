# Phase 2 — Anti-Slop Triage Plan

> **From:** `docs/_review/anti_slop_findings.md` (12 findings, AS-001 through AS-016)
> **Date:** 2026-05-28
> **Auditor:** Phase 2 automated triage (hostile AI-archaeology)

---

## Summary

12 findings triaged → **9 specs created** (8 severity-specific + 1 trivial bundle).

| Severity | Count | Specs Created |
|----------|-------|---------------|
| SCATHING-fundamentals | 1 | `AS-001-serialize-expand-bug.md` |
| SCATHING-readability | 1 | `AS-002-conftest-monkey-patch.md` |
| SEVERE | 2 | `AS-003-client-double-guard.md`, `AS-004-http-coverage-regression.md` |
| MEDIUM | 5 | `AS-005-integration-tests.md`, `AS-006-hypothesis-tests.md`, `AS-008-client-docstrings.md`, `AS-009-getting-started-table.md`, `AS-010-readme-marketing.md` |
| TRIVIAL (bundled) | 3 | `AS-CLEANUP-trivial-fixes.md` (AS-007, AS-011, AS-012) |
| CLEAN (no action) | 3 | AS-013 (F3), AS-014 (F4), AS-015 (F7), AS-016 (F8) |

---

## Spec Inventory

### SCATHING — Critical Path (Gate 1)

| # | Spec | File | Severity | Depends On | Existing SR Spec |
|---|------|------|----------|------------|-----------------|
| 1 | **AS-001** — Fix `_serialize.py:58` reading unfiltered query dict | `specs/AS-001-serialize-expand-bug.md` | SCATHING-fundamentals | None | SR-012 (OPEN) |
| 2 | **AS-002** — Remove monkey-patch from conftest.py mock_http | `specs/AS-002-conftest-monkey-patch.md` | SCATHING-readability | None | SR-007 (OPEN) |

### SEVERE — Gate 2

| # | Spec | File | Severity | Depends On | Existing SR Spec |
|---|------|------|----------|------------|-----------------|
| 3 | **AS-003** — Remove redundant `_entered` guard | `specs/AS-003-client-double-guard.md` | SEVERE | None | — |
| 4 | **AS-004** — Restore `_http.py` coverage to ≥ 85% | `specs/AS-004-http-coverage-regression.md` | SEVERE | None | SR-013 (OPEN) |

### MEDIUM — Gate 3

| # | Spec | File | Severity | Depends On | Existing SR Spec |
|---|------|------|----------|------------|-----------------|
| 5 | **AS-005** — Smoke integration test infrastructure | `specs/AS-005-integration-tests.md` | MEDIUM | None (but benefits from AS-002 for stable mocks) | SR-005 (OPEN) |
| 6 | **AS-006** — Property-based tests with Hypothesis | `specs/AS-006-hypothesis-tests.md` | MEDIUM | None (test-only) | SR-006 (OPEN) |
| 7 | **AS-008** — Rewrite generic docstrings in client.py | `specs/AS-008-client-docstrings.md` | MEDIUM | None | — |
| 8 | **AS-009** — Replace line-by-line table with WHY narrative | `specs/AS-009-getting-started-table.md` | MEDIUM | None | — |
| 9 | **AS-010** — Replace marketing-speak with evidence | `specs/AS-010-readme-marketing.md` | MEDIUM | None | — |

### TRIVIAL — Gate 4 (any order, bundled)

| # | Spec | File | Severity | Findings Bundled |
|---|------|------|----------|-----------------|
| 10 | **AS-CLEANUP** — Trivial fixes bundle | `specs/AS-CLEANUP-trivial-fixes.md` | TRIVIAL | AS-007 (redundant comments), AS-011 (Any cleanup), AS-012 (metadata stub) |

---

## Phase 3 Execution Order (Gates)

### Gate 1: SCATHING (must pass before Gate 2)

| Order | Task | File | Est. effort | Validated by |
|-------|------|------|-------------|-------------|
| 1a | **AS-001 TEST_RED** – Write test proving `query.get("$expand")` bug | `tests/unit/test_serialize_expand_bug.py` | 15 min | `./test-first-guard` |
| 1b | **AS-001 IMPL_GREEN** – Change line 58: `query` → `filtered` | `src/ado_odata_async/query/_serialize.py` | 1 min | `uv run pytest -q` |
| 1c | **AS-002 TEST_RED** – Write conftest refactor test | `tests/unit/test_mock_fixture.py` | 15 min | `./test-first-guard` |
| 1d | **AS-002 IMPL_GREEN** – Remove monkey-patch, use `replace=True` or ordering fix | `tests/conftest.py` | 20 min | `uv run pytest -q` |

**Gate 1 DoD:**
- [ ] AS-001 AC-1 through AC-4 GREEN
- [ ] AS-002 AC-1 through AC-5 GREEN
- [ ] `uv run pytest -q` exit 0
- [ ] `bash scripts/audit.sh` exit 0

### Gate 2: SEVERE

| Order | Task | File | Est. effort | Validated by |
|-------|------|------|-------------|-------------|
| 2a | **AS-003 TEST_RED** – Write entry/exit lifecycle tests | `tests/unit/test_client_entry_exit.py` | 15 min | `./test-first-guard` |
| 2b | **AS-003 IMPL_GREEN** – Remove `_entered`, keep only `_has_entered_once` | `src/ado_odata_async/client.py` | 10 min | `uv run pytest -q` |
| 2c | **AS-004 TEST_RED** – Write 8 new coverage tests | `tests/unit/test_http_coverage.py` | 30 min | `./test-first-guard` |
| 2d | **AS-004 COVERAGE_VERIFY** – Run coverage check (target ≥ 85%) | — | 2 min | `uv run pytest --cov=ado_odata_async._http --cov-fail-under=85` |

**Gate 2 DoD:**
- [ ] AS-003 AC-1 through AC-4 GREEN
- [ ] AS-004 AC-1 through AC-8 GREEN
- [ ] `uv run pytest --cov=ado_odata_async --cov-fail-under=85` exit 0
- [ ] `ruff check .` exit 0

### Gate 3: MEDIUM (parallelizable)

| Order | Task | File | Est. effort | Validated by |
|-------|------|------|-------------|-------------|
| 3a | **AS-005 IMPL** – Create `tests/integration/` + smoke test + pyproject marker | `tests/integration/`, `pyproject.toml` | 20 min | `uv run pytest tests/integration/ --run-integration` |
| 3b | **AS-006 IMPL** – Create Hypothesis property tests | `tests/unit/test_hypothesis.py` | 45 min | `uv run pytest -q tests/unit/test_hypothesis.py` |
| 3c | **AS-008 IMPL** – Rewrite client.py docstrings | `src/ado_odata_async/client.py` | 15 min | grep inspection per ACs |
| 3d | **AS-009 IMPL** – Replace line-by-line table | `docs/getting-started.md` | 15 min | grep inspection per ACs |
| 3e | **AS-010 IMPL** – Rewrite README claims | `README.md` | 15 min | grep inspection per ACs |

**Gate 3 DoD:**
- [ ] AS-005 AC-1 through AC-5 GREEN
- [ ] AS-006 AC-1 through AC-5 GREEN
- [ ] AS-008 AC-1 through AC-4 GREEN
- [ ] AS-009 AC-1 through AC-4 GREEN
- [ ] AS-010 AC-1 through AC-4 GREEN
- [ ] `uv run pytest -q` exit 0
- [ ] `ruff check .` exit 0
- [ ] `mypy src/ --strict` exit 0

### Gate 4: TRIVIAL (bundled, fastest)

| Order | Task | File | Est. effort | Validated by |
|-------|------|------|-------------|-------------|
| 4a | **AS-CLEANUP-007** – Shorten _http.py, client.py, _filter.py module docstrings | 3 files | 5 min | grep per ACs |
| 4b | **AS-CLEANUP-011** – Add `# noqa` or explanatory comment for Any usage (verify legitimacy) | `_http.py:6`, `client.py:8` | 5 min | grep per ACs |
| 4c | **AS-CLEANUP-012** – Add deferred-feature docstring to metadata.py | `src/ado_odata_async/metadata.py` | 2 min | read per AC |

**Gate 4 DoD:**
- [ ] AS-CLEANUP AC-1 through AC-5 GREEN
- [ ] `uv run pytest -q` exit 0
- [ ] `ruff check .` exit 0
- [ ] `bash scripts/audit.sh` exit 0

---

## Findings Not Spec'd

| Finding | Severity | Reason |
|---------|----------|--------|
| AS-011 (F6: typing.Any) | TRIVIAL false positive | Legitimate usage; bundled in AS-CLEANUP with comment-only fix |
| AS-013 (F3: lazy except) | CLEAN | No lazy except blocks found |
| AS-014 (F4: premature abstraction) | CLEAN | Filter DSL is appropriate for composable expressions |
| AS-015 (F7: tests that prove nothing) | CLEAN | Mock strategy is sound; implementation issue covered by AS-002 |
| AS-016 (F8: cosmetic concurrency) | CLEAN | No cosmetic concurrency found |

---

## Open SR Items Status

| SR | Finding | Covered By | Action |
|----|---------|-----------|--------|
| SR-005 | No integration tests | AS-005 | New spec created |
| SR-006 | No Hypothesis tests | AS-006 | New spec created |
| SR-007 | Mock fixture monkey-patch | AS-002 | New spec created |
| SR-012 | serialize reads original query | AS-001 | New spec created |
| SR-013 | _http.py error coverage | AS-004 | New spec created |
| SR-002 | Redundant validator | Not in B9 scope | Requires separate spec |
| SR-008 | `__setattr__` catches ValidationError | Not in B9 scope | Requires separate spec |
| SR-009 | Double filter in pagination | Not in B9 scope | Requires separate spec |
| SR-010 | Dead import in getting-started | Not in B9 scope | Requires separate spec |
| SR-011 | No timeout config | Not in B9 scope | Requires separate spec |
| SR-014 | Stale RED-phase docstrings | Not in B9 scope | Requires separate spec |
| SR-017 | Missing `__all__` | Not in B9 scope | Requires separate spec |
| SR-018 | Spec 012 AC | Not in B9 scope | Requires separate spec |

---

## B10 Trust-Ladder Violations (Documented, Not Spec'd)

| HR | Violation | Mitigation |
|----|-----------|------------|
| HR-3 (Test first) | VIOLATED — git log bundles test+impl | Accept SDD bundling OR add `@pytest.mark.xfail` pre-tests |
| HR-18 (git-keeper) | VIOLATED — `omo-agent` commits directly | Accept workflow OR refactor to use git-keeper exclusively |

These are process violations, not code issues. They are documented here for the retrospective (`/retro`) but do not require specs.

---

## File Count

| Category | Count |
|----------|-------|
| Specs created (≥ MEDIUM) | 8 |
| CLEAN findings (no action) | 4 |
| Specs created (TRIVIAL bundle) | 1 |
| **Total specs created** | **9** |
| **Total findings addressed** | **12** |
