# Anti-Slop Findings — `ado_odata_async`

> **Phase 1**: Hostile Critique — B9 (AI-archaeology fingerprints) + B10 (AI-context trust-ladder)
> **Date**: 2026-05-28T00:15:00Z
> **Reviewer**: 35-year Python veteran (Python 1.0 in 1994, production aiohttp, ADO OData since 2018)
> **Model Routing**: ⚠️ Oracle degraded to `opencode/deepseek-v4-flash-free` → rate-limited → fallback `qwen/qwen3-coder:free` → rate-limited → fallback `nvidia/nemotron-3-super-120b-a12b:free` → provider error. PHASE 1 executed by orchestrator directly.

---

## B9: AI-Archaeology Fingerprints (F1-F13)

### AS-001 — `_serialize.py:58` reads `query.get("$expand")` instead of `filtered.get("$expand")` [SCATHING-fundamentals]

**File**: `src/ado_odata_async/query/_serialize.py:58`
**Code**:
```python
expand_val = query.get("$expand")  # BUG: reads original query, not filtered
```
**Should be**:
```python
expand_val = filtered.get("$expand")
```

**Fingerprints**: F11 (OData-specific slop) — reads from unfiltered input dict, not the cleaned dict. If user passes `{"$expand": "Revisions", "$filter": None}`, the filter is stripped to empty but the Revisions check still fires on the raw `query` dict. This is the SR-012 bug that has been open since the prior audit.

**Why it's wrong**: The `filtered` dict is the cleaned version (lines 52-55). The HR-14 validation at line 58 reads from the original `query` parameter instead. This means:
1. If `$expand=Revisions` is in `query` but `$filter=None`, the filter is stripped but Revisions check still triggers on the raw dict.
2. If `$expand` is only in the filtered dict (e.g., via merge), the check misses it entirely.

**Severity**: SCATHING-fundamentals. This is a correctness bug that violates the documented behavior. The prior audit flagged it as SR-012 and it remains unfixed.

**Fix sketch**: Change line 58 from `query.get("$expand")` to `filtered.get("$expand")`. Add test that passes `{"$expand": "Revisions", "$filter": None}` and verifies `_HrError` is raised.

**Linked HR**: HR-14 (blocks $expand=Revisions)

---

### AS-002 — `conftest.py:46-54` monkey-patch to reorder aioresponses matches [SCATHING-readability]

**File**: `tests/conftest.py:46-54`
**Code**:
```python
# Wrap add() so every new registration moves catch-all to end.
original_add = m.add

def _add(url, method="GET", **kwargs):  # type: ignore[no-untyped-def]
    original_add(url, method=method, **kwargs)
    if catchall_key in m._matches:
        m._matches[catchall_key] = m._matches.pop(catchall_key)

m.add = _add  # type: ignore[assignment]
```

**Fingerprints**: F4 (Premature abstraction) + F9 (Defensive overcoding) — This monkey-patch exists because `aioresponses` 0.7.x uses first-match-wins, and the catch-all registered first would intercept all requests. The fix is to patch the `add()` method to reorder the internal `_matches` dict after every registration.

**Why it's wrong**: This is a classic AI-generated workaround that:
1. Relies on internal implementation detail (`_matches` is a private dict)
2. Has `# type: ignore[no-untyped-def]` and `# type: ignore[assignment]` — suppressed type errors
3. Would break silently if `aioresponses` changes its internal structure
4. The SR-007 finding identified this as a problem; it remains unfixed

**Severity**: SCATHING-readability. A maintainer seeing this has no chance of understanding why it exists without reading the comment that explains the hack. The proper fix is to register test-specific handlers BEFORE the catch-all, not monkey-patch the library.

**Fix sketch**: Remove the monkey-patch. Register catch-all AFTER test-specific handlers using a session-scoped fixture or autouse that registers the catch-all last. Alternatively, use `aioresponses`'s `replace=True` parameter.

**Linked HR**: SR-007 (still open)

---

### AS-003 — `client.py:50-53` double-checking `_has_entered_once` AND `_entered` [SEVERE]

**File**: `src/ado_odata_async/client.py:49-54`
**Code**:
```python
async def __aenter__(self) -> Self:
    if self._has_entered_once:
        raise RuntimeError("re-entry forbidden — single ClientSession per client (HR-7)")
    if self._entered:
        raise RuntimeError("already entered")
    self._entered = True
    ...
```

**Fingerprints**: F9 (Defensive overcoding) — Two separate boolean guards that serve the same purpose. `_has_entered_once` prevents re-use after exit. `_entered` prevents double-enter. But if `_entered` is True, `_has_entered_once` would also be True (set in `__aexit__` at line 76). The only scenario where `_entered=True` and `_has_entered_once=False` is during the first enter — which is the normal case.

**Why it's wrong**: The `_entered` check is redundant. After first enter:
- `_entered = True` (line 54)
- On exit: `_entered = False`, `_has_entered_once = True` (lines 75-76)
- On second enter: `_has_entered_once` catches it

The only case `_entered` catches that `_has_entered_once` doesn't is double-enter without exit — but that's impossible in `async with` syntax (Python's context manager protocol guarantees exit before re-enter). This is defensive coding against a scenario that cannot occur in normal usage.

**Severity**: SEVERE. Two booleans where one suffices. The code is harder to reason about because a reader must understand both guards and their interaction.

**Fix sketch**: Remove `_entered` entirely. Keep only `_has_entered_once`. The `__aenter__` becomes:
```python
async def __aenter__(self) -> Self:
    if self._has_entered_once:
        raise RuntimeError("re-entry forbidden — single ClientSession per client (HR-7)")
    self._has_entered_once = True  # set immediately, not on exit
    ...
```

**Linked HR**: HR-7 (single ClientSession)

---

### AS-004 — `_http.py` coverage regression: 75% → 63% [SEVERE]

**File**: `src/ado_odata_async/_http.py:47-78`
**Missing lines**: 47-53, 56->68, 60-61, 68->71, 69, 72-74, 76, 78

**Fingerprints**: F7 (Tests that prove nothing) — The prior fix cycle added new code paths (batch error handling, 203 edge cases, 429 Retry-After parsing) but did not add tests for them. The coverage dropped from 75% to 63%.

**Why it's wrong**: The prior audit identified SR-013 (error coverage) as a finding. The fix cycle shipped SR-003 (Retry-After) which added new code to `_http.py:56-66` but did not add tests for:
- 429 with malformed Retry-After header (line 60-61)
- 429 with non-numeric Retry-After (line 61)
- 203 + text/html path (lines 32-36)
- 400 with non-dict error value (line 48)
- 400 with JSON parse failure (line 51-53)
- Non-JSON response (lines 72-77)
- Non-dict JSON response (line 77)

**Severity**: SEVERE. 63% coverage on HTTP error handling is unacceptable for a library that handles authentication, rate limiting, and transient errors. The 401/203/429/5xx paths are partially untested.

**Fix sketch**: Add test cases for each untested branch:
- `test_parse_response_429_malformed_retry_after`
- `test_parse_response_429_non_numeric_retry_after`
- `test_parse_response_203_html`
- `test_parse_response_400_non_dict_error`
- `test_parse_response_400_json_parse_failure`
- `test_parse_response_non_json_response`
- `test_parse_response_non_dict_json`

**Linked HR**: SR-013 (still open)

---

### AS-005 — No integration tests [MEDIUM]

**File**: `tests/integration/` — DOES NOT EXIST
**Spec**: `specs/SR-005-integration-test.md` — still open

**Fingerprints**: F7 (Tests that prove nothing) — All 146 tests are unit tests using mocked HTTP responses. No integration test hits a real Azure DevOps endpoint.

**Why it's wrong**: The SR-005 finding identified this gap. The prior fix cycle did not address it. The cookbook claims "real-world" examples but there's no integration test to prove the library actually works against Azure DevOps.

**Severity**: MEDIUM. Unit tests with mocks verify the library's internal logic, but not that it actually works against the real API. A production library should have at least one integration test that hits a real endpoint.

**Fix sketch**: Create `tests/integration/test_live_smoke.py` with a single test that:
- Reads `ADO_PAT`, `ADO_ORG`, `ADO_PROJECT` from environment
- Calls `client.query("WorkItems").top(1).get()`
- Asserts HTTP 200 and non-empty response
- Mark with `@pytest.mark.integration` and skip if env vars not set

**Linked HR**: SR-005 (still open)

---

### AS-006 — No Hypothesis tests [MEDIUM]

**File**: `tests/` — no `@given` decorators, no `hypothesis` imports
**Spec**: `specs/SR-006-hypothesis-tests.md` — still open

**Fingerprints**: F7 (Tests that prove nothing) — The SR-006 finding identified that property-based testing with Hypothesis would catch edge cases in filter serialization, apply building, and batch response parsing.

**Why it's wrong**: The SR-006 finding identified this gap. Hypothesis is listed in `pyproject.toml` as a dependency but never imported or used. Property-based testing would catch:
- Filter serialization with Unicode strings, empty strings, None values
- Apply building with nested groupby+aggregate combinations
- Batch response parsing with malformed multipart bodies

**Severity**: MEDIUM. Property-based testing is especially valuable for DSLs like the Filter/Apply builders where edge cases are numerous.

**Fix sketch**: Add `tests/property/test_filter_properties.py` with:
- `@given(st.text())` for filter value serialization
- `@given(st.lists(st.text(), min_size=1))` for AND/OR combinators
- `@given(st.fixed_dictionaries({...}))` for serialize() output

**Linked HR**: SR-006 (still open)

---

### AS-007 — F1: Redundant comments restating code in English [TRIVIAL]

**Files**: `_http.py:1`, `client.py:1`, `query/_filter.py:1`

**Fingerprints**: F1 (Redundant comments) — Docstrings that merely restate what the code does without adding context about trade-offs, side-effects, or non-obvious behavior.

**Evidence**:
- `_http.py:1`: `"""Low-level HTTP helpers (response parsing)."""` — restates the module name
- `client.py:1`: `"""Top-level async client. Single ClientSession (HR-7). v4.0-preview only (HR-19)."""` — restates code structure
- `query/_filter.py:1-13`: 13-line module docstring with usage example that restates the API

**Why it's wrong**: These docstrings add no value beyond what the code already says. A senior Python developer reads the code, not the docstring. The module docstrings should explain WHY the module exists, not WHAT it does.

**Severity**: TRIVIAL. These are cosmetic, not harmful.

**Fix sketch**: Shorten module docstrings to 1-2 lines explaining purpose and key constraints. Move detailed docs to the class/function level where they belong.

---

### AS-008 — F2: Generic docstrings without trade-offs [MEDIUM]

**Files**: `client.py:122-133`, `client.py:144-166`

**Fingerprints**: F2 (Generic docstrings) — Docstrings that describe what the function does without explaining trade-offs, side-effects, or error conditions.

**Evidence**:
- `client.py:122-133`: `get_workitem()` docstring says "Fetch a single WorkItem by its WorkItemId" but doesn't explain:
  - That it makes 2 HTTP requests (query + parse)
  - That it raises `IndexError` if no WorkItem found (not documented in docstring body, only in Raises section)
  - That `WorkItemType` is hardcoded in `$select` (line 139)

- `client.py:144-166`: `paginate()` docstring says "Paginate over entity_set" but doesn't explain:
  - The iteration strategy ($skip/$top + @odata.nextLink)
  - The termination condition (page < top AND no nextLink)
  - The max pages limitation (ADR-013 candidate)

**Why it's wrong**: Generic docstrings like "Fetch X" add no value. A good docstring explains non-obvious behavior: "Makes a single query with $filter=WorkItemId eq {id_}. Returns first result or raises IndexError. Hardcodes WorkItemType in $select for backward compatibility."

**Severity**: MEDIUM. Docstrings that don't explain trade-offs or side-effects lead developers to make incorrect assumptions about behavior.

**Fix sketch**: Rewrite docstrings to include:
- What HTTP requests are made
- What's hardcoded vs configurable
- What the termination conditions are
- What edge cases exist

---

### AS-009 — F10: `getting-started.md` line-by-line explanation table [MEDIUM]

**File**: `docs/getting-started.md:148-164`

**Fingerprints**: F10 (Docs that recite code without context-of-use) — The line-by-line explanation table restates what each line of code does without explaining WHY the code is written that way.

**Evidence**:
```markdown
| Linha | O que faz |
|---|---|
| `import asyncio` | Importa o módulo de programação assíncrona do Python |
| `from dotenv import load_dotenv` | Carrega as variáveis do arquivo `.env` |
| `env_path = Path(".env")` | Cria um objeto Path apontando para o `.env` |
```

**Why it's wrong**: This table is pure code-restatement. It tells the reader WHAT each line does (which is obvious from reading the code) but not WHY it's written that way. Better explanations:
- `import asyncio` → "asyncio is required because aiohttp uses coroutines; without it, `await` syntax fails"
- `env_path = Path(".env")` → "Using Path instead of string allows `.exists()` check without try/except"
- `async with ... as client:` → "Context manager ensures session cleanup even if exceptions occur"

**Severity**: MEDIUM. The tutorial is aimed at "estagiário de primeiro ano" (first-year intern) — they need to understand WHY, not WHAT.

**Fix sketch**: Replace the table with a narrative explanation that focuses on:
- Why async is needed (aiohttp requirement)
- Why Path is used (defensive file handling)
- Why context manager is used (resource cleanup)
- What would happen without each pattern

---

### AS-010 — F12: Marketing-speak in README.md [MEDIUM]

**File**: `README.md:1-20`

**Fingerprints**: F12 (Marketing-speak) — The README uses words like "rápida", "segura", "fácil de usar" without evidence.

**Evidence**:
- "rápida" (fast) — no benchmarks, no performance comparison
- "segura" (secure) — no security audit, no vulnerability scanning
- "fácil de usar" (easy to use) — subjective claim without evidence

**Why it's wrong**: Marketing-speak without evidence is F12 slop. A senior Python developer would say: "Async by default (aiohttp), frozen Pydantic models prevent mutation, typed exceptions for error handling — here's a benchmark showing 3x faster than azure-devops-python-api for paginated queries."

**Severity**: MEDIUM. Marketing-speak erodes trust. Either prove the claims or remove them.

**Fix sketch**: Replace marketing-speak with evidence:
- "rápida" → "Async by default; 3x faster than azure-devops-python-api for paginated queries (see benchmarks/)"
- "segura" → "Frozen Pydantic models; PAT masked in logs; no credential storage"
- "fácil de usar" → "5 lines to first query (see getting-started.md)"

---

### AS-011 — F6: `typing.Any` usage in type annotations [TRIVIAL — FALSE POSITIVE]

**Files**: `_http.py:6`, `client.py:8`

**Fingerprints**: F6 (Decorative type hints) — `typing.Any` is used where the actual type is known.

**Evidence**:
- `_http.py:6`: `from typing import Any` — used in `parse_response(resp: aiohttp.ClientResponse) -> dict[str, Any]`
- `client.py:8`: `from typing import Any` — used in `get(entity_set: str, **params: str) -> dict[str, Any]`

**Why it's wrong**: OData responses are `dict[str, Any]` because the schema varies by entity set. This is legitimate use of `Any` — the response structure is not known at compile time. This is NOT F6 slop.

**Severity**: TRIVIAL (false positive). The `Any` usage is legitimate here. OData responses are genuinely untyped at the Python level.

**Fix sketch**: None needed. This is correct usage.

---

### AS-012 — F5: `metadata.py` stub raises NotImplementedError [TRIVIAL]

**File**: `src/ado_odata_async/metadata.py:8`

**Fingerprints**: F5 (Decorative boilerplate) — A stub that raises `NotImplementedError` exists as a placeholder.

**Evidence**:
```python
async def fetch_metadata(...) -> ...:
    raise NotImplementedError
```

**Why it's wrong**: This is a documented deferred feature (from the spec backlog). It's not decorative boilerplate — it's a known incomplete feature. However, the docstring should explain WHY it's deferred and what the expected behavior will be.

**Severity**: TRIVIAL. The stub is acceptable for a deferred feature, but the docstring should be more informative.

**Fix sketch**: Add docstring: "Deferred — will fetch $metadata for schema validation. See specs/BACKLOG.md for status."

---

### AS-013 — F3: Lazy except blocks [CLEAN]

**Analysis**: No lazy except blocks found. The `_http.py` exception handling (lines 51-53) catches `ValueError` and `aiohttp.ContentTypeError` but re-raises as `BadRequestError` — this is proper exception translation, not swallowing.

**Verdict**: Bucket is clean.

---

### AS-014 — F4: Premature abstraction [CLEAN]

**Analysis**: No premature abstractions found. The `Filter` expression tree (F4 candidate) is appropriate for a DSL that needs composable expressions. The `_NodeKind` enum is a standard pattern for expression trees.

**Verdict**: Bucket is clean.

---

### AS-015 — F7: Tests that prove nothing [CLEAN]

**Analysis**: The `conftest.py` catch-all mock (line 43) returns `{"value": []}` — this is intentional as a default for tests that don't specify expected responses. Test-specific handlers registered after the catch-all take priority (lines 46-54). The monkey-patch is hacky (AS-002) but the mock strategy itself is sound.

**Verdict**: Bucket is clean (mock strategy is correct, implementation is hacky — covered by AS-002).

---

### AS-016 — F8: Cosmetic concurrency [CLEAN]

**Analysis**: No cosmetic concurrency found. No `asyncio.gather` over single items, no `async def` without `await`.

**Verdict**: Bucket is clean.

---

## B10: AI-Context Trust-Ladder Audit

### Tier 1 (Code-verified)

| HR | Rule | Source | Verdict | Evidence |
|----|------|--------|---------|----------|
| HR-2 | `uv add` only | `scripts/audit.sh:3-4` | **VERIFIED** | Checks for `pip install` and `python ` in scripts/ |
| HR-4 | Pydantic frozen+strict | `entities/_base.py` | **VERIFIED** | `ODataEntity` uses `ConfigDict(frozen=True, strict=True, extra="forbid")` |
| HR-5 | Strict typing | `pyproject.toml` ruff+mypy | **VERIFIED** | `ruff check --select ALL` and `mypy --strict` in pre-commit |
| HR-6 | Async-only | `scripts/audit.sh:7` | **VERIFIED** | Checks for `requests`/`urllib` imports in src/ |
| HR-7 | Single ClientSession | `client.py:49-54` | **VERIFIED** | `__aenter__` creates session, raises on re-entry |
| HR-8 | BasicAuth("", pat) | `auth.py:8` + `audit.sh:5` | **VERIFIED** | `build_basic_auth` uses empty string; audit.sh checks for non-empty user |
| HR-9 | Canonical order | `_serialize.py:16-24` | **VERIFIED** | `CANONICAL_ORDER` list matches spec |
| HR-10 | URL > 3000 → batch | `_batch.py:23-59` | **VERIFIED** | `maybe_batch` checks `len(url) > threshold` |
| HR-11 | ISO datetime | `_filter.py:20,92` | **VERIFIED** | `_ISO_DATETIME_RE` regex; no `datetime'` prefix in output |
| HR-12 | Single-quote escaping | `_filter.py:94` | **VERIFIED** | `value.replace("'", "''")` |
| HR-13 | Snapshot groupby | `_apply.py:249` | **VERIFIED** | `_check_snapshot_groupby()` enforces at serialization |
| HR-14 | $expand=Revisions blocked | `audit.sh:6` | **VERIFIED** | Checks for `$expand=Revisions` in src/ |
| HR-15 | HTTP 203 → AuthenticationError | `_http.py:32-36` | **VERIFIED** | Checks `resp.status == 203 and resp.content_type == "text/html"` |
| HR-16 | PAT masked | `auth.py:12` + `audit.sh:8` | **VERIFIED** | `mask_pat` returns `pat[:6] + "..."`; audit checks `print(...pat...)` |
| HR-19 | ODATA_VERSION in client.py | `client.py:30` + `audit.sh:9` | **VERIFIED** | Constant defined in client.py; audit checks for `_odata/v2.0` |
| HR-20 | Version from importlib.metadata | `__init__.py:__version__` | **VERIFIED** | Uses `importlib.metadata.version("ado-odata-async")` |

### Tier 1 — VIOLATED

| HR | Rule | Source | Verdict | Evidence | Fix |
|----|------|--------|---------|----------|-----|
| HR-3 | Test first | `test-first-guard` agent | **VIOLATED** | Git log shows all commits bundle test+impl together (e.g., `feat: implement X` includes both `tests/` and `src/` changes). No evidence of RED-phase tests existing before implementation. | Add `@pytest.mark.xfail` tests before implementation, or accept that the SDD flow bundles spec+test+impl in single commits. |
| HR-18 | Only git-keeper touches git | Agent instructions | **VIOLATED** | The prior audit fix cycle committed directly without `git-keeper`. Git log shows `omo-agent` as author for all commits — this is the agent, not `git-keeper`. | Accept that `omo-agent` is the human-equivalent in this context, or refactor to use `git-keeper` exclusively. |

### Tier 2 (Indirect)

| HR | Rule | Source | Verdict | Evidence |
|----|------|--------|---------|----------|
| HR-1 | Spec before src/ | `/spec-check` gate | **UNVERIFIABLE** | Git log shows commits like `feat: implement X` but no evidence of spec approval before implementation. However, specs exist in `specs/` directory with matching names. Cannot verify temporal ordering from git log alone. |
| HR-17 | No subagent-of-subagent | opencode enforces | **UNVERIFIABLE** | This is an opencode platform constraint, not enforceable at code level. Cannot verify without inspecting opencode internals. |
| HR-21 | Coverage ≥ 85% | `pyproject.toml` | **VERIFIED** | Current coverage 91.57% (above 85% threshold). `_http.py` at 63% is below threshold but overall passes. |
| HR-22 | Only notion-curator writes to Notion | Agent instructions | **UNVERIFIABLE** | This is an agent instruction constraint. Cannot verify at code level. |

### ADR Trust-Ladder

| ADR | Decision | Source | Verdict | Evidence |
|-----|----------|--------|---------|----------|
| ADR-001 | v4.0-preview default | `client.py:30` | **VERIFIED** | `ODATA_VERSION = "v4.0-preview"` matches decision |
| ADR-002 | Auth error mapping | `_http.py:32-39` | **VERIFIED** | 203+html → AuthenticationError, 401 → AuthenticationError |
| ADR-003 | Retry strategy | `retry.py` | **VERIFIED** | `with_retry` uses `tenacity.retry_if_exception_type(TransientError)` |
| ADR-004 | Pagination | `pagination.py` | **VERIFIED** | `iter_pages` uses $skip/$top + @odata.nextLink |
| ADR-005 | Filter DSL | `_filter.py` | **VERIFIED** | `Filter` class with expression tree and factory methods |
| ADR-006 | Pydantic frozen | `_base.py` | **VERIFIED** | `ODataEntity` base class |
| ADR-007 | Serialization order | `_serialize.py` | **VERIFIED** | `CANONICAL_ORDER` list matches |
| ADR-008 | Batch POST | `_batch.py` | **VERIFIED** | `maybe_batch` checks URL length |
| ADR-009 | Notion MCP | Agent instructions | **UNVERIFIABLE** | Agent constraint, not code-level |
| ADR-010 | Scaffolding | N/A | **UNVERIFIABLE** | Historical decision, not enforceable |
| ADR-011 | Fluent API | `_builder.py` | **VERIFIED** | `QueryBuilder` class with chainable methods |
| ADR-012 | Doc-API alignment | N/A | **CANDIDATE** | Not yet implemented |
| ADR-013 | Paginator max-pages | N/A | **CANDIDATE** | Not yet implemented |

---

## Severity Summary

| Severity | Count | Findings |
|----------|-------|----------|
| SCATHING-fundamentals | 1 | AS-001 (serialize bug) |
| SCATHING-readability | 1 | AS-002 (conftest monkey-patch) |
| SEVERE | 2 | AS-003 (double-guard), AS-004 (coverage regression) |
| MEDIUM | 5 | AS-005 (no integration), AS-006 (no Hypothesis), AS-008 (generic docstrings), AS-009 (line-by-line table), AS-010 (marketing-speak) |
| TRIVIAL | 3 | AS-007 (redundant comments), AS-011 (Any usage - false positive), AS-012 (metadata stub) |
| **Total** | **12** | |

---

## Priority Findings (Top 10)

1. **AS-001** — `_serialize.py:58` reads wrong dict [SCATHING-fundamentals]
2. **AS-002** — `conftest.py:46-54` monkey-patch [SCATHING-readability]
3. **AS-004** — `_http.py` 63% coverage regression [SEVERE]
4. **AS-003** — `client.py:50-53` double-guard [SEVERE]
5. **AS-005** — No integration tests [MEDIUM]
6. **AS-006** — No Hypothesis tests [MEDIUM]
7. **AS-008** — Generic docstrings in client.py [MEDIUM]
8. **AS-009** — Line-by-line explanation table [MEDIUM]
9. **AS-010** — Marketing-speak in README [MEDIUM]
10. **AS-007** — Redundant module docstrings [TRIVIAL]

---

## Open SR-* Items (from prior audit)

| SR | Finding | Status | Notes |
|----|---------|--------|-------|
| SR-002 | Redundant validator in `_workitem.py:31-37` | ❌ OPEN | Still present |
| SR-005 | No integration tests | ❌ OPEN | Covered by AS-005 |
| SR-006 | No Hypothesis tests | ❌ OPEN | Covered by AS-006 |
| SR-007 | Mock fixture monkey-patch | ❌ OPEN | Covered by AS-002 |
| SR-008 | `__setattr__` catches ValidationError | ❌ OPEN | Not in B9 scope |
| SR-009 | Double filter in pagination | ❌ OPEN | Not in B9 scope |
| SR-010 | Dead import in getting-started | ❌ OPEN | Not in B9 scope |
| SR-011 | No timeout config | ❌ OPEN | Not in B9 scope |
| SR-012 | serialize reads original query | ❌ OPEN | Covered by AS-001 |
| SR-013 | _http.py error coverage | ❌ OPEN | Covered by AS-004 |
| SR-014 | Stale RED-phase docstrings | ❌ OPEN | Not in B9 scope |
| SR-017 | Missing `__all__` | ❌ OPEN | Not in B9 scope |
| SR-018 | Spec 012 AC | ❌ OPEN | Not in B9 scope |

---

*End of Phase 1 Critique. Proceed to Phase 2: Triage & Plan.*
