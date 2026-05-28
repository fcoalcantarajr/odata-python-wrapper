# Phase 0 Inventory — Senior Python Veteran Audit

**Date**: 2026-05-27
**Auditor role**: 35-year Python vet, Azure DevOps OData specialist
**Baseline**: F12 merge committed (groupby+aggregate nesting, countdistinct block)

---

## Codebase Snapshot

| Metric | Value |
|--------|-------|
| Source files (.py) | 21 |
| Test files (.py) | 15 |
| Test coverage | 89.33% (above 85% threshold) |
| Last commits | F12 merge + F11 apply fixes + F10 ordering |
| Test status | 128 pass, 0 fail |

---

## Public Symbols by Module

### Core Classes
- **`AdoODataClient`** (`client.py`): single-entry async context manager (HR-7)
- **`QueryBuilder`** (`query/_builder.py`): fluent query construction
- **`Filter`** (`query/_filter.py`): $filter expression tree builder
- **`Apply`** (`query/_apply.py`): $apply groupby/filter/aggregate builder
- **`ODataEntity`** (base, `entities/_base.py`): frozen+strict Pydantic base

### Exception Hierarchy
- `AdoODataError` (base)
- `AuthenticationError` (not retryable)
- `BadRequestError` (not retryable)
- `TransientError` (retryable)
- `RateLimitError` (TransientError, capped retry)

### Entity Models (21 total, frozen+strict+extra-forbid)
- WorkItem, WorkItemRevision, WorkItemSnapshot
- WorkItemBoardSnapshot, WorkItemBoard
- Identity, UserTeam, TeamMember, AssignedTo, CreatedBy, ChangedBy, ResolvedBy, ClosedBy
- Team, Project, Area, Iteration
- Others: Reference subclasses

### Functions
- **`build_basic_auth(pat)`**: returns `BasicAuth("", pat)` per HR-8
- **`mask_pat(pat)`**: returns `pat[:6] + "..."` per HR-16
- **`with_retry(fn, max_attempts, min_delay, max_delay)`**: tenacity decorator, retries TransientError only (HR-15)
- **`parse_response(resp)`**: maps HTTP → typed exceptions per gotchas 1, 8
- **`serialize(query)`**: canonical order + HR-14 $expand check
- **`maybe_batch(method, url, threshold, service_root)`**: URL > 3000 → POST $batch switch
- **`build_batch_get_body(queries)`**: multipart/mixed batch builder
- **`parse_batch_response(text)`**: multipart/mixed response parser

---

## Documentation Assets (SHA256 locked)

| File | SHA256 | Lines | Purpose |
|------|--------|-------|---------|
| HANDOFF.md | `ee9db7...` | 115 | Phase handoff notes (F11→F12) |
| architecture.md | `5c8333...` | 66 | High-level component overview |
| concepts.md | `8da3b4...` | 297 | OData 101, WorkItems vs Revisions vs Snapshot |
| cookbook.md | `c1486e...` | 562 | 8 recipes (auth, pagination, filtering, batch, $apply, etc) |
| decisions.md | `631a5b...` | 127 | ADRs: v4.0-preview adoption, Pydantic frozen strict, etc |
| getting-started.md | `63e4c1...` | 197 | Setup + first query walkthrough |
| glossary.md | `659345...` | 244 | Term definitions (WorkItem, Snapshot, OData, etc) |
| troubleshooting.md | `eff8f8...` | 255 | 10 common errors with root causes + fixes |

---

## Test Suite Baseline

**All 128 tests PASS. Coverage: 89.33%**

### Test Modules (by feature spec)
- `test_http_skeleton.py`: HTTP response parsing → exceptions (gotchas 1, 8)
- `test_auth_error_mapping.py`: 401 / 203+HTML → AuthenticationError (HR-15, gotcha 1)
- `test_retry_tenacity.py`: TransientError retry, RateLimitError cap, no AuthenticationError retry
- `test_filter_dsl.py`: Filter.eq/and_/or_/not_/contains builders, quote escaping (HR-12 gotcha 6), ISO datetime (HR-11 gotcha 7)
- `test_serialize.py`: Canonical order ($apply → $filter → ...), $expand=Revisions block (HR-14 gotcha 5)
- `test_apply_dsl.py`: groupby/filter/aggregate builders, countdistinct block, nested groupby+aggregate (F12)
- `test_batch.py`: URL > 3000 → POST $batch (HR-10 gotcha 3), multipart/mixed parsing
- `test_pagination.py`: cursor iteration, pagination through large result sets
- `test_client_integration.py`: full end-to-end async context manager flow
- `test_fluent_api.py`: QueryBuilder fluent chain (.query / .filter / .select / .get / .batch)
- `test_workitem_entity.py`: WorkItem Pydantic model, frozen + strict validation
- `test_remaining_entities.py`: snapshot entities, board entities, reference entities
- `test_stubs_coverage.py`: runtime stub file consistency check (HR-20)

---

## HARD RULES Enforcement Status

| HR | Title | Enforced | Mechanism |
|----|-------|----------|-----------|
| HR-1 | Spec → code | ✅ | Commits reference F00-F12 specs |
| HR-2 | `uv` only, no `pip` | ✅ | `audit.sh` blocks `pip install` |
| HR-3 | Test RED first | ✅ | Specs require RED→GREEN cycle |
| HR-4 | Pydantic frozen+strict | ✅ | ODataEntity base enforces ConfigDict |
| HR-5 | Strict typing | ✅ | mypy --strict enforced, no bare `# type: ignore` |
| HR-6 | Async aiohttp only | ✅ | `audit.sh` blocks `requests` / `urllib` |
| HR-7 | Single ClientSession | ✅ | AdoODataClient context manager + re-entry guard |
| HR-8 | BasicAuth("", pat) | ✅ | `build_basic_auth` hardcoded empty user |
| HR-9 | Query option order | ✅ | `serialize()` enforces canonical order |
| HR-10 | URL > 3000 → $batch | ✅ | `maybe_batch()` implements switch |
| HR-11 | ISO 8601 no prefix | ✅ | Filter._format_value detects ISO regex |
| HR-12 | Quote escaping '' | ✅ | Filter._format_value.replace("'", "''") |
| HR-13 | Snapshot groupby | ⚠️ | Apply.validate() checks DateSK/DateValue presence (no test coverage yet) |
| HR-14 | No $expand=Revisions | ✅ | `serialize()` raises _HrError if Revisions detected |
| HR-15 | Auth ≠ retry | ✅ | parse_response() raises AuthenticationError (not TransientError), with_retry() only retries TransientError |
| HR-16 | PAT masking | ✅ | `mask_pat()` + logger calls use mask_pat() |
| HR-17 | No subagent→subagent | N/A | Not an agent codebase (Python library) |
| HR-18 | Only git-keeper touches git | N/A | No agent code |
| HR-19 | Version isolated constant | ✅ | ODATA_VERSION in client.py |
| HR-20 | pyproject.toml truth | ✅ | Version "0.0.1" + test for importlib.metadata consistency |
| HR-21 | Coverage ≥ 85% | ✅ | 89.33% baseline |
| HR-22 | Only notion-curator → MCP | N/A | No MCP integration |

---

## 8 OData Gotchas: Enforcement Verification

| Gotcha | Title | Status | Location |
|--------|-------|--------|----------|
| 1 | BasicAuth empty user | ✅ | `auth.py:8` |
| 2 | Query option order | ✅ | `query/_serialize.py:CANONICAL_ORDER` |
| 3 | URL > 3000 → $batch | ✅ | `query/_batch.py:maybe_batch()` |
| 4 | Snapshot groupby DateSK/DateValue | ⚠️ | `query/_apply.py:validate()`, but no end-to-end test |
| 5 | $expand=Revisions blocked | ✅ | `query/_serialize.py:serialize()` |
| 6 | Quote escaping '' | ✅ | `query/_filter.py:_format_value()` |
| 7 | ISO 8601 no `datetime'` prefix | ✅ | `query/_filter.py:_format_value()`, regex match |
| 8 | HTTP 203 + text/html → AuthenticationError ✅ | N/A | `_http.py:parse_response()` |
| **NEW** | countdistinct banned | ✅ | `query/_apply.py:aggregate()` raises NotImplementedError (F12) |

---

## Gaps & Preliminary Observations

1. **HR-13 Snapshot groupby** (`validate()`) — called in tests but unclear if end-to-end WorkItemSnapshot queries actually test this.
2. **Missing `.env.example`** — should document expected env vars (ADO_ORG, ADO_PROJECT, ADO_PAT).
3. **Retry logic clarity** — `with_retry()` wraps functions, but `parse_response()` raises exceptions directly. Flow is: `parse_response()` → exception → `with_retry()` catches if TransientError. Correct but convoluted.
4. **Batch endpoint construction** — `maybe_batch()` expects `service_root` param, but in real code flow, check where it's called.
5. **Docs drift on countdistinct** — troubleshooting.md still shows examples with countdistinct in "WRONG" section (good), but `cookbook.md` might have stale recipes.

---

## Next Phase: Phase 1 (Findings)

Will audit:
- **B1**: Async correctness (session lifetime, cancellation)
- **B2**: Pydantic + typing consistency
- **B3**: Retry backoff sanity
- **B4**: OData gotchas enforcement + edge cases
- **B5**: Docs vs runtime drift
- **B6**: Test coverage gaps
- **B7**: Production readiness (PAT leaks, audit.sh gate)
- **B8**: SDD/TDD discipline

---

**End of Phase 0 Inventory**
