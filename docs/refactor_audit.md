# SOLID + PEP-8 Refactor Audit

Date: 2026-06-05
Scope: `src/ado_odata_async/` (14 source files)

Baseline: 192 passed, 2 skipped | 96.29% coverage | ruff clean | mypy --strict clean | audit.sh pass

---

## Findings (ordered by severity)

### HIGH-1: `client.py:96-129` — `get()` god method (SRP)

**What**: `AdoODataClient.get()` does 5 things in one method body:
1. Query string serialization (line 101)
2. URL construction (lines 102-104)
3. Batch decision (lines 106-108)
4. HTTP execution — POST branch (lines 114-122) AND GET branch (lines 124-125)
5. Error wrapping (lines 126-129)

**Violation**: SRP — one method = one reason to change. But each of these 5 concerns can change independently.

**Concrete cut**: Extract an `_execute_request` method that takes method + URL and handles batch/GET branching + response parsing. `get()` becomes: serialize → construct URL → delegate to `_execute_request`.

**Test seam**: Already covered by `test_client_integration.py` (100% coverage of this path). No new test needed — just verify existing tests pass after refactor.

---

### HIGH-2: `pagination.py:42-45` — Direct `_session` access (SRP + Demeter)

**What**: `iter_pages()` accesses `client._session` directly to follow `@odata.nextLink` URLs (lines 42-45), bypassing the client's public API entirely.

**Violation**: Law of Demeter + SRP. `pagination.py` knows about `ClientSession` internals. If the session lifecycle changes, pagination breaks.

**Concrete cut**: Add a `_get_raw(url: str)` method to `AdoODataClient` that fetches a URL by its full path (for nextLink). `pagination.py` calls `client._get_raw(next_link_url)` instead of reaching into `_session`.

**Test seam**: Already covered by `test_pagination.py`. No new test needed.

---

### MEDIUM-1: `query/_apply.py:60-169` — Dual-role class/instance methods (SRP + ISP)

**What**: `Apply.groupby()`, `filter()`, and `aggregate()` detect whether they're called on the class or an instance via `isinstance(self, Apply)`. When called on the class (e.g. `Apply.groupby("State")`), `self` is the first argument (the field), not an `Apply` instance.

**Violation**: SRP — each method has two completely different code paths depending on call context. ISP — users see one interface but it behaves differently.

**Concrete cut**: Split into class methods (`@classmethod`) and instance methods. `Apply.groupby()` becomes a `@classmethod` that returns a new `Apply`. Instance `.groupby()` is a separate method on the instance. This removes the `isinstance(self, Apply)` checks entirely.

**Test seam**: All 50+ tests in `test_apply_dsl.py` exercise both paths. No new test needed — they must all pass.

**NOTE**: This is the riskiest refactor. The dual-role pattern is intentional (documented in comments). Must verify all test_apply_dsl.py tests pass.

---

### MEDIUM-2: `entities/_base.py:20-30` — `__setattr__` override (NOT dead code — SKIP)

**What**: `ODataEntity.__setattr__` catches `ValidationError` and re-raises as `TypeError` with "immutable" message.

**Assessment**: This is NOT dead code. Test `test_workitem_entity.py:ac5_frozen_prevents_mutation` asserts `TypeError` with `match="immutable"`. Pydantic v2 with `frozen=True` raises `ValidationError`, not `TypeError`. The override converts it for backward compatibility.

**Decision**: SKIP — this is intentional compatibility layer, not cruft. Removing it would break test AC-5 and change the public error contract.

---

### MEDIUM-3: `client.py:127` — Lazy import inside except block (PEP-8 style)

**What**: `from ado_odata_async.exceptions import TransientError` is inside the `except aiohttp.ClientError` block (line 127-128). This is a lazy import to avoid circular dependency.

**Violation**: PEP-8 — imports should be at top of file. This lazy import exists because `exceptions.py` is in the same package. It's actually fine from a circular dep perspective — `client.py` already imports from `auth.py`, `_http.py`, `entities/`, `pagination.py`, `query/`, `retry.py` at the top. The `exceptions` import was moved inside to avoid... actually there's no circular dep reason. `exceptions.py` imports nothing from the package.

**Concrete cut**: Move `from ado_odata_async.exceptions import TransientError` to the top-level imports.

**Test seam**: No test needed — pure import location change.

---

### LOW-1: `query/_apply.py:84,103,148` — `type: ignore[unreachable]` comments

**What**: Three `# type: ignore[unreachable]` comments for the class-level code paths that only execute when `self` is not an `Apply` instance.

**Violation**: Style / readability. These are necessary because of the dual-role pattern. If MEDIUM-1 is fixed, these disappear.

**Concrete cut**: Resolved by MEDIUM-1 refactor.

---

### LOW-2: `pagination.py:50-55` — Query param construction duplication

**What**: `iter_pages()` builds query params manually (lines 50-55) instead of using the serializer or builder.

**Violation**: Minor duplication. The logic is simple (merge dict, add $skip, $top) but duplicates what the serializer does.

**Concrete cut**: None needed — this is a simple dict merge, not duplicated serialization logic. The serializer is called by `client.get()`. YAGNI.

---

### Modules already clean (no action needed)

| Module | Assessment |
|--------|-----------|
| `_http.py` | Clean SRP — single function, clear error mapping |
| `auth.py` | Clean — two pure functions, no coupling |
| `retry.py` | Clean — well-separated wait/stop/wrap |
| `exceptions.py` | Clean — simple hierarchy, correct inheritance |
| `metadata.py` | Clean — stub with clear docstring |
| `query/_serialize.py` | Clean — single responsibility, canonical order |
| `query/_batch.py` | Clean — pure functions, well-documented |
| `query/_builder.py` | Clean — immutable builder, proper delegation |
| `query/_filter.py` | Clean — expression tree, proper factory methods |
| `entities/_reference.py` | Clean — simple data models |
| `entities/_system.py` | Clean — simple data models |
| `entities/_workitem.py` | Clean — proper validator |
| `entities/_workitemrevisions.py` | Clean — simple data model |
| `entities/_board.py` | Clean — simple data models |

---

## Summary

| Severity | Count | Action |
|----------|-------|--------|
| HIGH | 2 | Must fix — real SRP/Demeter violations with test seams |
| MEDIUM | 3 | Fix 2 (MEDIUM-1, MEDIUM-3), SKIP 1 (MEDIUM-2 — intentional compat layer) |
| LOW | 2 | Skip — YAGNI / resolved by MEDIUM-1 |

**Estimated scope**: 4 real changes (HIGH-1, HIGH-2, MEDIUM-1, MEDIUM-3).
