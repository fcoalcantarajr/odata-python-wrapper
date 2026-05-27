# Senior Audit Findings — `ado_odata_async`

**Date**: 2026-05-27  
**Reviewer**: 35-year Python veteran (Python 1.0 in 1994, production aiohttp, ADO OData since 2018)  
**Scope**: All 21 source files in `src/ado_odata_async/`, 14 test files, 8 docs, 12 specs, config files  
**Severity distribution**: 2 SCATHING, 5 SEVERE, 6 MEDIUM, 3 TRIVIAL

---

## Summary by Bucket

| Bucket | Title | Findings | Worst Severity |
|--------|-------|----------|----------------|
| **B1** | Async correctness | SR-001, SR-009, SR-011 | SCATHING |
| **B2** | Pydantic & typing | SR-002, SR-008 | MEDIUM |
| **B3** | Retry/backoff | SR-003, SR-016 | SEVERE |
| **B4** | OData domain truth | SR-004, SR-012 | SCATHING |
| **B5** | Docs vs reality | SR-005, SR-010, SR-014 | SEVERE |
| **B6** | Test rigor | SR-006, SR-007, SR-013, SR-015 | SEVERE |
| **B7** | Production-readiness | SR-011 shared, SR-016 shared | MEDIUM |
| **B8** | SDD/TDD discipline | SR-014 shared | MEDIUM |

---

## B1 — Async Correctness

### SR-001 — SCATHING — `iter_pages()` accesses `client._session` with lying comment, no guard

**File**: `src/ado_odata_async/pagination.py:42`

```python
async with client._session.get(next_link_url) as resp:  # type: ignore[union-attr]  # reason: session exists during iteration (guarded by self._fetched)
```

**Why it's wrong**: This is junior-grade. The comment says "guarded by `self._fetched`" — but `self._fetched` doesn't exist anywhere in the codebase. There is no guard. If the caller's `async for page in client.paginate(...)` loop outlives the `async with AdoODataClient(...)` context manager, `client._session` is `None` and this line explodes with `AttributeError: 'NoneType' object has no attribute 'get'`.

PEP 492 and PEP 533 explicitly warn that async generators holding resource references must be consumed before the context exits. This code ignores that.

A dedicated RED-phase test (`tests/unit/test_sr_001_pagination_session.py`) *expects* a `RuntimeError` for this scenario, but the production code never delivers it. The test is perpetually RED by design — that's not a fix, that's a TODO list.

**Fix**: Add a `None` check on `client._session` before accessing it:

```python
if client._session is None:
    raise RuntimeError("session closed — pagination must complete before client context exits")
async with client._session.get(next_link_url) as resp:
```

Or better: capture the session reference at generator creation time so it doesn't dangle.

**Hard rules**: HR-7 (single ClientSession), HR-3 (test first — test exists but code never implemented)

---

### SR-009 — MEDIUM — `iter_pages()` accepts unused `query` parameter, then mutates it

**File**: `src/ado_odata_async/pagination.py:47-53`

```python
merged: dict[str, str] = {}
if query:
    merged.update(query)
```

**Why it's wrong**: The function accepts `query: dict[str, str] | None` then copies into a local dict. This is correct for avoiding mutation of the caller's dict. But at line 53 it calls `client.get(entity_set, **merged)` which goes through `serialize()` — and `serialize()` also filters `None` and `""` values. So there's a double filter: once at call time (line 52), once inside `serialize()` (`_serialize.py:52`). Not a bug, but wasteful and suggests confusion about where filtering should live.

**Fix**: Document that `serialize()` handles filtering, or remove the pre-filter:

```python
def _merge_query(self, query: dict[str, str] | None) -> dict[str, str]:
    merged = dict(query) if query else {}
    ...
```

**Hard rules**: None directly.

---

### SR-011 — SEVERE — No request timeout configuration

**File**: `src/ado_odata_async/client.py:55`

```python
self._session = aiohttp.ClientSession(auth=build_basic_auth(self._pat))
```

**Why it's wrong**: The `ClientSession` is created with zero timeout configuration. `aiohttp` default total timeout is 5 minutes (`aiohttp.ClientTimeout(total=300)`). If ADO hangs (which happens — I've seen 60s+ response times on `WorkItemBoardSnapshot`), the caller blocks for 5 minutes with no way to interrupt.

There is no `ClientTimeout` parameter on `AdoODataClient.__init__()`. Users who need a shorter timeout must either:
1. Subclass and override `__aenter__` (won't — too complex)
2. Set `aiohttp.ClientTimeout` globally (side-effect on other sessions)
3. Wrap everything in `asyncio.wait_for()` (clunky)

**Fix**: Accept optional `ClientTimeout` in `__init__()` with a sensible default (30s connect, 60s total):

```python
def __init__(self, *, org: str, project: str, pat: str,
             batch_threshold: int = 3000,
             timeout: aiohttp.ClientTimeout | None = None) -> None:
    self._timeout = timeout or aiohttp.ClientTimeout(total=60, connect=30)
    ...
    self._session = aiohttp.ClientSession(auth=build_basic_auth(self._pat),
                                          timeout=self._timeout)
```

**Hard rules**: None directly.

---

## B2 — Pydantic & Typing Rigor

### SR-002 — MEDIUM — `WorkItem.field_validator` duplicates `Literal` type constraint

**File**: `src/ado_odata_async/entities/_workitem.py:31-37`

```python
WORK_ITEM_TYPES: tuple[str, ...] = ("Bug", "User Story", "Task", "Feature", "Epic")

class WorkItem(ODataEntity):
    WorkItemType: Literal["Bug", "User Story", "Task", "Feature", "Epic"]

    @field_validator("WorkItemType")
    @classmethod
    def _validate_work_item_type(cls, v: str) -> str:
        if v not in WORK_ITEM_TYPES:
            msg = f"WorkItemType must be one of {WORK_ITEM_TYPES}, got {v!r}"
            raise ValueError(msg)
        return v
```

**Why it's wrong**: The `Literal` type already constrains `WorkItemType` to exactly those five strings. The `field_validator` is entirely redundant. Pydantic v2 enforces `Literal` types natively — if `WorkItemType` gets a value outside the literal, it raises `ValidationError` with a clear message. The validator adds no value, just maintenance burden: if you add "Initiative" to `WORK_ITEM_TYPES`, you must update both the `Literal` and the tuple. DRY violation.

**Severity**: MEDIUM because it works, it's just pointless code.

**Fix**: Remove the validator and the `WORK_ITEM_TYPES` tuple. Let Pydantic's `Literal` type do the work:

```python
class WorkItem(ODataEntity):
    WorkItemId: int = Field(gt=0)
    Title: str
    WorkItemType: Literal["Bug", "User Story", "Task", "Feature", "Epic"]
```

**Hard rules**: HR-4 (frozen+strict — yes, but also violates implicit DRY principle).

---

### SR-008 — TRIVIAL — `__setattr__` override in `ODataEntity` catches wrong exception

**File**: `src/ado_odata_async/entities/_base.py:20-30`

```python
def __setattr__(self, name: str, value: Any) -> None:
    try:
        super().__setattr__(name, value)
    except ValidationError as exc:
        msg = f"'{type(self).__name__}' object is immutable"
        raise TypeError(msg) from exc
```

**Why it's wrong**: In Pydantic v2, setting an attribute on a frozen model raises `FrozenInstanceError`, which is a subclass of `ValidationError`. So this *works*, but it's fragile. If Pydantic v3 changes the error hierarchy, this breaks silently. The spec (AC-5) demands `TypeError` with `"immutable"` — but that's an artificial requirement that works against the ecosystem.

The real issue: this converts a well-known Pydantic error into a generic `TypeError` that users won't recognize. Every Pydantic user knows what `ValidationError` means. Few will recognize `TypeError` + "immutable".

**Fix**: Either (a) accept Pydantic's native `FrozenInstanceError` and update the tests, or (b) catch the specific exception type:

```python
from pydantic import ValidationError
# Pydantic v2 uses FrozenInstanceError which is a subclass of ValidationError
```

**Hard rules**: HR-4 (frozen+strict — this is the enforcement mechanism).

---

## B3 — Retry/Backoff Sanity

### SR-003 — SEVERE — `Retry-After` header is completely ignored on 429

**File**: `src/ado_odata_async/retry.py:56-62`

```python
retry_decorator = tenacity_retry(
    stop=_stop,
    wait=wait_exponential_jitter(initial=min_delay, max=max_delay),
    retry=retry_if_exception_type(TransientError),
    ...
)
```

**File**: `src/ado_odata_async/_http.py:56-58`

```python
if resp.status == 429:
    retry_after = resp.headers.get("Retry-After", "unknown")
    raise RateLimitError(f"HTTP 429: Rate limit. Retry-After: {retry_after}s")
```

**Why it's wrong**: The `parse_response` function faithfully reads the `Retry-After` header from 429 responses, puts it in the error message as a string — and then the retry decorator completely ignores it. The `wait_exponential_jitter` computes a delay between 0.5s and 10s regardless of what the server says.

Azure DevOps rate limits are aggressive. The `Retry-After` header might say 60 seconds. The current code retries after 0.5s → gets another 429 → retries after ~1s → gets another 429 → retries after ~2s → gets another 429 → gives up after 3 attempts, all within ~3.5 seconds. The server said "wait 60s" and we ignored it.

This is worse than useless — it burns through retry budget faster, making the rate limiting worse.

**Fix**: Use a custom `tenacity.wait` that reads the `Retry-After` value from the exception's message or, better, store it as an attribute on `RateLimitError`:

```python
class RateLimitError(TransientError):
    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after
```

Then in the retry decorator:

```python
def _wait_rate_limit_aware(retry_state: RetryCallState) -> float:
    outcome = retry_state.outcome
    if outcome and outcome.exception():
        exc = outcome.exception()
        if isinstance(exc, RateLimitError) and exc.retry_after is not None:
            return exc.retry_after + 0.5  # small buffer
    return wait_exponential_jitter(initial=min_delay, max=max_delay)(retry_state)
```

**Hard rules**: HR-15 (retryable exceptions — yes, but Retry-After is protocol-level, not HR).

---

### SR-016 — MEDIUM — `RateLimitError` cap logic is fragile

**File**: `src/ado_odata_async/retry.py:43-54`

```python
rate_limit_max = min(max_attempts, 3)

def _stop(retry_state: RetryCallState) -> bool:
    if retry_state.attempt_number >= max_attempts:
        return True
    if retry_state.attempt_number >= rate_limit_max:
        outcome = retry_state.outcome
        if outcome is not None:
            exc = outcome.exception()
            if exc is not None and isinstance(exc, RateLimitError):
                return True
    return False
```

**Why it's wrong**: The cap is `min(max_attempts, 3)` — which is 3 when `max_attempts=5`. But the check at line 46 hits `True` when `attempt_number >= max_attempts` (5). So for a `RateLimitError` with `max_attempts=5`, the function retries 5 times, not 3, because line 46 catches everything >= 5 before line 48 gets a chance. The RateLimit cap only works when `rate_limit_max < max_attempts` — which it is (3 < 5), but line 46 fires first once attempt 5 is reached.

Wait — let me trace this:
- Attempt 1: `attempt_number=1`, not stopped
- Attempt 2: `attempt_number=2`, not stopped  
- Attempt 3: `attempt_number=3`, `rate_limit_max=3`, `3 >= 3` is True, checks if RateLimitError → True → stops

OK, so when `attempt_number == 3`, line 46 hasn't fired yet (3 < 5), and line 48 fires. The cap *does* work at 3 attempts for `RateLimitError` with `max_attempts=5`. Let me re-check...

The issue is when `max_attempts=3` and it's a `RateLimitError`:
- Attempt 1: `attempt_number=1`, not stopped
- Attempt 2: `attempt_number=2`, not stopped
- Attempt 3: `attempt_number=3`, `3 >= 3` True → line 46 stops it BEFORE line 48 checks for RateLimitError

So when `max_attempts=3` and `rate_limit_max=3`, the `TransientError` stop fires first, and the `RateLimitError`-specific code at line 48-53 is dead code in this case. Not a bug but confusing and suggests the logic wasn't carefully designed.

Actually, that's exactly right — both stop conditions fire at attempt 3. The RateLimit-specific check only matters when `max_attempts > 3`. This is logically correct but unnecessarily confusing.

**Fix**: Simplify the stop logic:

```python
def _stop(retry_state: RetryCallState) -> bool:
    if retry_state.attempt_number >= max_attempts:
        return True
    return False
```

Then set `max_attempts` based on the exception type at decoration time won't work because we don't know the exception type at decoration time. The current logic is tight enough that this is a MEDIUM at best.

**Hard rules**: None.

---

## B4 — OData Domain Truth

### SR-004 — SCATHING — HR-13 validation is implemented three separate ways, none sharing code

**File**: `src/ado_odata_async/query/_apply.py:175-198` (`Apply.validate()`)
**File**: `src/ado_odata_async/query/_builder.py:70-93` (`QueryBuilder.apply()`)
**File**: `src/ado_odata_async/query/_builder.py:137-156` (`QueryBuilder._validate_hr13()`)

This is the most glaring code quality issue in the entire project.

**Validation path 1**: `Apply(entity_type="WorkItemSnapshot").validate()` — checks `entity_type` attribute, checks groupby fields in `_operations`.

**Validation path 2**: `QueryBuilder.apply(a)` — takes the `Apply` instance BUT **does not pass entity_type to it**. Instead, the builder has its own `self._entity_set` and does its own regex parsing of the `build()` output string.

**Validation path 3**: `QueryBuilder._validate_hr13()` — called by `get()` and `paginate()`. Same regex pattern, same logic, different method.

So when a user writes `client.query("WorkItemSnapshot").apply(Apply(...)).get()`, the HR-13 check runs **three times**: once in `Apply.validate()` (if entity_type was set, which it wasn't — so this doesn't fire), once in `builder.apply()`, and once in `builder._validate_hr13()`. That's up to 2 redundant checks.

And the regex is duplicated in `apply()` and `_validate_hr13()`:
```python
m = re.search(r"groupby\(\(([^)]+)\)\)", apply_val)
```

If the groupby syntax ever changes (e.g., to support nested computed properties), you need to update 3 places.

**Fix**: Delegate to a single function:

```python
def _check_snapshot_groupby(entity_set: str, apply_value: str) -> None:
    required = {"WorkItemSnapshot": "DateSK", "WorkItemBoardSnapshot": "DateValue"}.get(entity_set)
    if required is None:
        return
    m = re.search(r"groupby\(\(([^)]+)\)\)", apply_value)
    if not m or required not in [f.strip() for f in m.group(1).split(",")]:
        raise ValueError(f"{entity_set} requires $apply with groupby(({required})) per HR-13")
```

Then call it from all three places.

**Hard rules**: HR-13 (enforcement design — currently over-engineered and under-maintained).

---

### SR-012 — MEDIUM — `serialize()` accesses `$expand` before filtering None/empty values

**File**: `src/ado_odata_async/query/_serialize.py:52,58`

```python
filtered: dict[str, str] = {k: v for k, v in query.items() if v is not None and v != ""}

if not filtered:
    return ""

# HR-14: $expand=Revisions is blocked (gotcha 5)
expand_val = query.get("$expand")  # <--- reads from ORIGINAL query, not filtered
```

**Why it's wrong**: Line 58 reads `$expand` from the original `query` dict, not from the `filtered` dict. If `$expand` is `""`, the HR-14 check at line 59-64 returns early because `if expand_val:` is False. So it *works*, but it's sloppy. It violates the principle that you either filter first and use the filtered version everywhere, or you don't filter at all. Using `query` for one check and `filtered` for everything else is a smell.

**Fix**: Read from `filtered`:

```python
expand_val = filtered.get("$expand")
```

**Hard rules**: HR-14 (Revisions block — still enforced, just sloppily).

---

## B5 — Docs vs Reality

### SR-005 — SEVERE — Cookbook claims "all recipes tested against real ADO" — no integration tests exist

**File**: `docs/cookbook.md:3-4`

> Todas as receitas abaixo usam código testado e funcionam com dados reais do Azure DevOps.

**File**: `pyproject.toml:83-84`

```toml
markers = [
    "integration: marca testes que batem em serviço real (skip por default)",
]
```

**Why it's wrong**: The integration marker exists in `pyproject.toml` but is used **zero times** in the entire test suite. There is no `tests/integration/` directory. No test has `@pytest.mark.integration`. The marker definition is dead code.

The cookbook claims all recipes are "tested and work with real data from Azure DevOps". There is no evidence of this. Either:
1. Someone manually ran each recipe against a live ADO project (unverifiable)
2. The claim is aspirational, not factual

For users in a regulated bank environment, "tested" means "CI passes with real credentials." CI never runs integration tests. The claim is misleading.

**Fix**: Either (a) remove the claim and mark recipes as "illustrative pseudocode, not tested against live ADO", or (b) write at least one integration test that validates the full stack against a real ADO endpoint, gated behind `@pytest.mark.integration`.

---

### SR-010 — MEDIUM — `getting-started.md` imports `Filter` but never uses it

**File**: `docs/getting-started.md:124`

```python
from ado_odata_async.query import Filter
```

Then proceeds to `client.query("WorkItems").select(...).top(5).get()` without calling any `Filter` method. Dead import in documentation — gives the wrong impression that `Filter` is required.

**Fix**: Remove the unused import:

```python
from ado_odata_async import AdoODataClient
```

---

### SR-014 — MEDIUM — 37 test docstrings claim "RED phase" — all actually pass

**Files**: `tests/unit/test_retry_tenacity.py:1-4`, `tests/unit/test_pagination.py:1-5`, `tests/unit/test_serialize.py:1-5`, `tests/unit/test_batch.py:1-5`, `tests/unit/test_remaining_entities.py:1-4`

Example from `test_filter_dsl.py:3-4`:
> All 10 tests MUST fail (RED) because `ado_odata_async.query._filter.Filter` does not exist yet.

`Filter` exists. The import works. All 10 tests pass. The docstring is a lie.

This is a documentation-versus-reality drift that erodes trust. A junior reading these docstrings will think the code doesn't exist. A senior will think the tests don't run. Both are wrong.

**Fix**: Update all RED-phase docstrings to reflect current status:

```python
"""Tests for SPEC-005 Filter DSL — all GREEN (was RED phase, code now implemented)."""
```

Or remove the RED-phase comments entirely.

---

## B6 — Test Rigor

### SR-006 — SEVERE — Hypothesis is a dev dependency but never used

**File**: `pyproject.toml:30`

```toml
"hypothesis>=6.112,<7",
```

**Evidence**: `rg "from hypothesis" tests/` — zero results. `rg "@given" tests/` — zero results. `rg "hypothesis" tests/` — zero results.

**Why it's wrong**: Hypothesis is installed in every developer environment, added to `uv sync --all-groups`, but has never been imported. This is dead weight.

More importantly, this codebase *screams* for property-based testing:
- **Filter DSL**: `Filter.build()` output → roundtrip parse → verify structure preserved
- **Serialize ordering**: All 5,040 permutations of 7 canonical options → verify order invariant
- **Entity validation**: Random data → verify strict typing enforcement
- **URL encoding**: Edge characters, Unicode, long strings → verify `%20` not `+`
- **Batch parsing**: Malformed multipart bodies → verify error handling

None of this is tested. The mocks are hand-crafted, which means they test only what the author thought of. Property-based testing would find edge cases no human considered.

**Fix**: Either (a) write at least one `@given` test (start with `serialize()` — it's pure and has a clear invariant), or (b) remove hypothesis from dependencies with an explanation.

---

### SR-007 — SEVERE — `mock_http` fixture monkey-patches `aioresponses` internals

**File**: `tests/conftest.py:38-55`

```python
@fixture
def mock_http() -> Iterator[aioresponses]:
    with aioresponses() as m:
        m.get(re.compile(r".*"), repeat=True, payload={"value": []})
        catchall_key: str = next(iter(m._matches))

        original_add = m.add
        def _add(url, method="GET", **kwargs):
            original_add(url, method=method, **kwargs)
            if catchall_key in m._matches:
                m._matches[catchall_key] = m._matches.pop(catchall_key)
        m.add = _add  # type: ignore[assignment]
        yield m
```

**Why it's wrong**: This accesses `m._matches` (a private attribute) and monkey-patches `m.add`. This is fragile across `aioresponses` versions. The comment says "aioresponses 0.7.x uses first-match-wins over _matches dict" — this is an implementation detail that could change in any patch release.

A junior wrote this workaround because they registered a catch-all first, then realized test-specific handlers had lower priority. The correct solution is to register the catch-all LAST, not to hack the internals.

**Fix**: Register the catch-all at the end, not the beginning:

```python
@fixture
def mock_http() -> Iterator[aioresponses]:
    with aioresponses() as m:
        yield m  # let tests register their handlers first
    # No catch-all — tests should be explicit about what they mock
```

If a catch-all is really needed, use `aioresponses`'s `passthrough` parameter or a separate fixture for the catch-all.

---

### SR-013 — MEDIUM — Coverage gap in error-path code

**Coverage report**: `_http.py:75%`, `client.py:83%`, `query/_builder.py:73%`

These are exactly the error-handling paths that matter most in production:
- `_http.py:47-53` — 400 body parsing fallback when JSON is malformed. Untested.
- `_http.py:65-69` — Non-JSON 200 response (shouldn't happen, but when it does, untested).
- `client.py:100-110` — POST `$batch` error handling. Untested.
- `client.py:115-116` — `ClientError` → `TransientError` translation. Untested.
- `query/_builder.py:79-89` — HR-13 in `apply()`. Untested.
- `query/_builder.py:146-154` — HR-13 in `_validate_hr13()`. Untested.

**Why it's wrong**: 11 of the 12 specs implement "happy path" logic. The error paths — where real production pain lives — are systematically under-tested. A network timeout, a malformed batch response, or a non-JSON 200 will produce cryptic errors.

**Fix**: Add tests for each untested line. Minimum:
1. `_http.py`: Mock a 200 with non-JSON body → expect `BadRequestError`
2. `_http.py`: Mock a 400 with non-JSON body → expect `BadRequestError` with fallback message
3. `client.py`: Mock `session.post` failure on batch path → expect `TransientError`
4. `_builder.py`: Feed `WorkItemSnapshot` without `groupby` → expect `ValueError`

---

### SR-015 — TRIVIAL — RED-phase test for SR-001 never turns GREEN

**File**: `tests/unit/test_sr_001_pagination_session.py`

```python
async def test_pagination_after_context_exit_raises_runtime_error(...):
    async with client:
        pass
    with pytest.raises(RuntimeError, match="session"):
        async for _ in client.paginate("WorkItems", top=100):
            pass
```

**Why it's wrong**: This test expects `RuntimeError` but the code at `pagination.py:42` will raise `AttributeError` (accessing `.get()` on `None`). The test will fail, not pass. It was written as a "RED phase" test to define the desired behavior, but unlike the other RED-phase tests, the code hasn't been written to make it pass. The test is aspirational — it's been RED since creation and will stay RED until someone fixes `iter_pages`.

This is not how TDD works. TDD is RED → GREEN → REFACTOR. Staying RED indefinitely is "test that documents a bug," not "test that drives development."

**Fix**: Either (a) fix the production code to make this test pass (see SR-001 fix), or (b) mark it `xfail` with a clear reason:

```python
@pytest.mark.xfail(reason="SR-001: iter_pages needs session-None guard before nextLink access")
```

---

## B7 — Production-Readiness

### Shared with B1/B3: SR-011 (no timeout) and SR-016 (Retry-After ignored)

### SR-017 — TRIVIAL — No `__all__` in submodules

**Files**: `src/ado_odata_async/entities/_workitem.py`, `src/ado_odata_async/entities/_board.py`, etc.

**Why it's wrong**: The top-level `__init__.py` has proper `__all__`, but individual entity modules have no `__all__`. When someone does `from ado_odata_async.entities._workitem import *`, they get all public names — but there's no contract. Minor, but inconsistent with the project's emphasis on strictness.

**Fix**: Add `__all__` to each entity module.

---

## B8 — SDD/TDD Discipline Drift

### SR-014 (shared with B5) — RED-phase docstrings lie about test status

Already documented above.

### SR-018 — MEDIUM — Spec 012 (Docs + ADRs) has no acceptance criteria in the testing sense

**File**: `specs/012-docs-adrs.md`

**Why it's wrong**: Spec 012 produced docs and ADRs but has no corresponding test file and no machine-verifiable acceptance criteria. The ADR-012 (doc-check) is a CANDIDATE that was never implemented. The spec's acceptance criteria are human-review-based, which means they rot silently (as evidenced by SR-005, SR-010, SR-014).

**Fix**: Add a minimal doctest-style check that extracts Python code from `.md` files and verifies imports resolve + API calls match method signatures. This is exactly what ADR-012 proposes but was never actioned.

---

## Summary of Actionable Items (Priority Order)

| Priority | SR-ID | Severity | Bucket | Title | Fix Type | Effort |
|----------|-------|----------|--------|-------|----------|--------|
| **P0** | SR-001 | SCATHING | B1 | `iter_pages` session-None guard | Code + test | Short |
| **P0** | SR-004 | SCATHING | B4 | HR-13 validation triplication | Refactor | Short |
| **P0** | SR-003 | SEVERE | B3 | `Retry-After` ignored on 429 | Code | Medium |
| **P1** | SR-006 | SEVERE | B6 | Hypothesis unused (use it or lose it) | Test + config | Medium |
| **P1** | SR-007 | SEVERE | B6 | Mock HTTP fixture monkey-patches internals | Test refactor | Short |
| **P1** | SR-005 | SEVERE | B5 | Cookbook lies about integration testing | Docs + infra | Medium |
| **P1** | SR-011 | SEVERE | B1 | No request timeout configuration | Code | Short |
| **P2** | SR-002 | MEDIUM | B2 | Redundant field_validator on WorkItemType | Code | Quick |
| **P2** | SR-012 | MEDIUM | B4 | `serialize()` reads original query not filtered | Code | Quick |
| **P2** | SR-013 | MEDIUM | B6 | Coverage gaps in error paths | Test | Medium |
| **P2** | SR-010 | MEDIUM | B5 | Dead import in getting-started.md | Docs | Quick |
| **P2** | SR-014 | MEDIUM | B5/B8 | 37 stale RED-phase docstrings | Docs | Short |
| **P2** | SR-018 | MEDIUM | B8 | Spec 012 lacks machine-verifiable AC | Docs + infra | Medium |
| **P3** | SR-009 | MEDIUM | B1 | `iter_pages` double-filter in query params | Code | Quick |
| **P3** | SR-015 | TRIVIAL | B6 | SR-001 RED test permanently failing | Test | Quick |
| **P3** | SR-008 | TRIVIAL | B2 | `__setattr__` catches wrong exception type | Code | Quick |
| **P3** | SR-016 | MEDIUM | B3 | RateLimit cap logic confusing | Code | Quick |
| **P3** | SR-017 | TRIVIAL | B7 | Missing `__all__` in entity submodules | Code | Quick |

---

## Buckets with No Findings

### B2 (partial) — Typing rigor on type ignores
✅ All `# type: ignore` instances in the codebase are properly tagged with specific error codes and `# reason:` comments. No bare ignores. No `Any` abuse in public API surfaces. The `# type: ignore[unreachable]` in `_apply.py` for the dual-role class/instance pattern is hacky but intentional and well-documented.

### B4 (partial) — 6 of 8 gotchas are correctly enforced
✅ Gotchas 1 (PAT empty), 2 (query order), 3 (batch), 5 (Revisions), 6 (quote escape), 7 (ISO datetime), 8 (203+html) are all enforced in code. The `scripts/audit.sh` grep patterns catch literal violations. Good discipline here.

### B7 (partial) — PAT masking is consistent
✅ `mask_pat()` is called in every log/print context. No bare PAT in `__repr__`, debug logs, or error messages. `audit.sh` catches `print(...pat...)` in `src/`.

---

## Final Verdict

This codebase has the *structure* of a well-engineered project — specs, HARD RULES, typed exceptions, Pydantic rigor, pre-commit gates, coverage threshold. These are all good things.

But the *substance* has three deep problems:

1. **Async lifecycle misunderstanding** (SR-001, SR-011): The core async pattern — session lifecycle in `iter_pages` — is wrong and the lying comment (`# guarded by self._fetched`) suggests someone didn't understand the bug and wrote a misleading explanation instead of a fix.

2. **Over-engineering without unification** (SR-004): HR-13 validation is implemented three ways because two different people added it to two different classes without talking to each other. This is a communication failure in the codebase.

3. **Tests that test what's easy, not what's hard** (SR-003, SR-005, SR-006, SR-007, SR-013): The test suite has 128 tests but doesn't test `Retry-After` behavior, integration, property-based invariants, or most error paths. Coverage is 89% but the uncovered lines are exactly the ones that fail in production.

The senior inventory called this "89.33% coverage, 128 tests passing." I call it "128 tests that prove the happy path works and the error paths are untested." These are different things.

The antidote: fix the P0 items (session guard, HR-13 dedup, Retry-After), then start treating the 11 uncovered error-path lines as a debt that must be paid before the next feature.
