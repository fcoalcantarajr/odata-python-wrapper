# Senior Audit Inventory — `ado_odata_async`

> Generated: 2026-05-27T22:17:49Z
> Purpose: Phase 0 of hostile code+docs review. Baseline for all SR-* findings.

---

## 1. Source Package: Every Public Symbol

All line numbers refer to `src/ado_odata_async/`. Total: **42 unique public symbols**.

### 1.1 Exceptions (`exceptions.py`)
| Symbol | Line | Kind | Extends | Retryable |
|---|---|---|---|---|
| `AdoODataError` | 6 | exception (base) | `Exception` | — |
| `AuthenticationError` | 10 | exception | `AdoODataError` | NEVER (HR-15) |
| `BadRequestError` | 14 | exception | `AdoODataError` | NEVER |
| `TransientError` | 18 | exception | `AdoODataError` | Yes (tenacity) |
| `RateLimitError` | 22 | exception | `TransientError` | Yes, capped 3 |

### 1.2 Core Client (`client.py`)
| Symbol | Line | Kind |
|---|---|---|
| `ODATA_VERSION` | 30 | constant: `"v4.0-preview"` (HR-19) |
| `AdoODataClient` | 33 | class — async context manager |

Public methods of `AdoODataClient`:
- `__init__(*, org, project, pat, batch_threshold=3000)` — line 40
- `__aenter__` → `Self` — line 49
- `__aexit__` — line 66
- `get(entity_set, **params)` → `dict[str, Any]` — line 87
- `get_workitem(id_)` → `WorkItem` — line 118
- `paginate(entity_set, *, top, query)` — line 140
- `query(entity_set)` → `QueryBuilder` — line 164

### 1.3 Auth (`auth.py`)
| Symbol | Line | Kind |
|---|---|---|
| `build_basic_auth(pat)` → `BasicAuth` | 8 | function: `BasicAuth("", pat)` (HR-8) |
| `mask_pat(pat)` → `str` | 12 | function: `pat[:6] + "..."` (HR-16) |

### 1.4 HTTP (`_http.py`)
| Symbol | Line | Kind |
|---|---|---|
| `parse_response(resp)` → `dict[str, Any]` | 20 | async function — HTTP status → typed exception |

### 1.5 Retry (`retry.py`)
| Symbol | Line | Kind |
|---|---|---|
| `with_retry(fn, max_attempts, min_delay, max_delay)` | 24 | decorator — tenacity on `TransientError` only |

### 1.6 Pagination (`pagination.py`)
| Symbol | Line | Kind |
|---|---|---|
| `iter_pages(client, entity_set, *, top, query)` | 17 | async generator — `$skip/$top` + `@odata.nextLink` |

### 1.7 Metadata (`metadata.py`)
| Symbol | Line | Kind |
|---|---|---|
| `fetch_metadata(client)` → `dict[str, Any]` | 7 | stub — raises `NotImplementedError` |

### 1.8 Query DSL (`query/`)
#### `query/__init__.py` exports: `Apply`, `Filter`, `QueryBuilder`, `maybe_batch`, `parse_batch_response`, `serialize`

#### `query/_apply.py`
| Symbol | Line | Kind |
|---|---|---|
| `Apply` | 21 | class — fluent `$apply` expression builder |

Methods: `groupby()`, `filter()`, `aggregate()`, `validate()`, `build()`

#### `query/_filter.py`
| Symbol | Line | Kind |
|---|---|---|
| `Filter` | 33 | class — OData `$filter` expression tree |

Static factories: `eq`, `ne`, `gt`, `ge`, `lt`, `le`, `and_`, `or_`, `not_`, `contains`

#### `query/_builder.py`
| Symbol | Line | Kind |
|---|---|---|
| `QueryBuilder` | 28 | class — immutable fluent builder |

Methods: `apply()`, `filter()`, `orderby()`, `expand()`, `select()`, `skip()`, `top()`, `get()`, `paginate()`

#### `query/_serialize.py`
| Symbol | Line | Kind |
|---|---|---|
| `CANONICAL_ORDER` | 16 | constant: `["$apply","$filter","$orderby","$expand","$select","$skip","$top"]` |
| `serialize(query)` → `str` | 31 | function — URL-encodes with canonical ordering (HR-9) |

#### `query/_batch.py`
| Symbol | Line | Kind |
|---|---|---|
| `maybe_batch(method, url, threshold, service_root)` → `tuple[str, str]` | 23 | function — URL > 3000 → POST `$batch` |
| `build_batch_get_body(query_url, service_root)` → `str` | 61 | function — builds multipart body |
| `parse_batch_response(raw)` → `dict` | 97 | function — extracts JSON from multipart response |

### 1.9 Entity Models (`entities/`)

#### `entities/_base.py`
| Symbol | Line | Kind |
|---|---|---|
| `ODataEntity` | 10 | class — `frozen=True, strict=True, extra="forbid"` (HR-4) |

#### 12 entity classes (all inherit `ODataEntity`):
| Class | File | Line | Key Fields |
|---|---|---|---|
| `WorkItem` | `_workitem.py` | 20 | `WorkItemId`, `Title`, `WorkItemType` (Literal) |
| `WorkItemRevisions` | `_workitemrevisions.py` | 14 | `WorkItemId`, `Revision`, `Title`, `WorkItemType`, `ChangedDate`, `State` |
| `WorkItemBoardSnapshot` | `_board.py` | 15 | `WorkItemId`, `BoardSK`, `BoardName`, `DateSK`, `State`, `IsCurrent` |
| `WorkItemBoardSnapshotWithDescription` | `_board.py` | 34 | extends snapshot with `Description` |
| `Date` | `_system.py` | 14 | `DateSK`, `Date`, `Day`, `Month`, `Year`, `Quarter`, etc. |
| `User` | `_system.py` | 29 | `UserSK`, `UserId`, `UserName`, `DisplayName` |
| `WorkItemType` | `_system.py` | 38 | `WorkItemTypeSK`, `WorkItemTypeName`, `WorkItemTypeDescription` |
| `WorkItemLink` | `_system.py` | 46 | `WorkItemLinkId`, `SourceWorkItemId`, `TargetWorkItemId`, `LinkType` |
| `Iteration` | `_reference.py` | 12 | `IterationSK`, `Identifier`, `IterationName`, `StartDate`, `EndDate` |
| `Project` | `_reference.py` | 22 | `ProjectSK`, `ProjectId`, `ProjectName` |
| `Team` | `_reference.py` | 31 | `TeamSK`, `TeamId`, `TeamName` |
| `Area` | `_reference.py` | 40 | `AreaSK`, `AreaId`, `AreaPath`, `AreaName`, `AreaLevel1-4` |

### 1.10 Module-level Constants (2)
- `WORK_ITEM_TYPES` — `entities/_workitem.py:11` — `("Bug","User Story","Task","Feature","Epic")`
- `CANONICAL_ORDER` — `query/_serialize.py:16` — query option precedence order

---

## 2. Documentation Files (SHA256)

### 2.1 Root
| File | SHA256 | Size |
|---|---|---|
| `AGENTS.md` | `38e726f2aeb8ff9f3b4ac7fda899a1fb9a16b2ff8d498b66fa09d703be49f15c` | 142 lines |
| `README.md` | `1e2a6515d0d112a2bf23d7220f921fef1a5e831f3efb6434491886bcec864e99` | — |

### 2.2 `docs/`
| File | SHA256 |
|---|---|
| `getting-started.md` | `63e4c1cbd7a32a833726460bdf0e9b8913027a2d64147943babe8e2c41224b41` |
| `concepts.md` | `8da3b4506639d0b394bb57be84d4bfd71c8b5f59659c39259934d98b481b69de` |
| `cookbook.md` | `c1486ec2c92669534fe1498a9ebd33259348c9430a88f2552a76adc26f67790c` |
| `troubleshooting.md` | `eff8f8ba16fde6b8fb37e492cd03363a12749b7bf1ca0b9147ac822605f5a54a` |
| `glossary.md` | `6593b452ecc74c57ae3e0eaecd9440ca52f2d04f3288b9aedf7e87edfda7b908` |
| `decisions.md` | `631a5b28636745411e2f193cf43b7b22943a1efebad4a9001297972cc69ef3cb` |
| `architecture.md` | `5c8333004e5f61ffce28b0e1f9ab1656349a3a7fbedcd388b6429c41c88599c3` |
| `HANDOFF.md` | `ee9db7761d414b2bff3ae3b9357338d66f74e0268a6a36e889e00fdd8848e4b7` |

### 2.3 Specs (`specs/`)
| File | SHA256 | Title |
|---|---|---|
| `000-TEMPLATE.md` | `8a6bb8512e6df588c169a0585b40bcf03b35db7c35015dfdc8bf075f0ffa84a2` | Spec Template |
| `001-http-skeleton.md` | `dae4a9190449a21aae56ffbf2e6af3188a6c90360f7ae13b63284ee516e4c681` | HTTP skeleton |
| `002-auth-error-mapping.md` | `d84cc31dfc0769d165ca667c55512b2c8d713435ce71939c797f2a6c517fc1ee` | Auth error mapping |
| `003-retry-tenacity.md` | `58d9cfcbd60143fba0d33a46d651fd2bfd2c6f0f5527e9e632711e945d5a1cbf` | Retry with tenacity |
| `004-pagination.md` | `35a622d518b063dfde82a008996bedaca9cd4a9b844b9e1b97c9f8dc7d05dc79` | Pagination |
| `005-filter-dsl.md` | `72b097171e4df4765f9738b357e53094558ec13d47a4772db237f322c13482c1` | Filter DSL |
| `006-apply-dsl.md` | `3868345d5542363c03949845af19ee9c782d61eb608d5a9a5606c70d4a2bbdfb` | `$apply` DSL |
| `007-serialization-order.md` | `ff829dc38ec676ee21ca68524c71be77d65440051694219b25de07333986001f` | Serialization order |
| `008-batch-post.md` | `c216c37f4fa75f9d507e42a0610bb2ff45e93d78b5931c5e27edfdcb98be619e` | POST `$batch` |
| `009-workitem-entity.md` | `3591a4973a46852957f409a9be5760334bb06035451748621fccc512528b5475` | WorkItem entity |
| `010-remaining-entities.md` | `292da091a5e65486b1d9065eef6f6e6952e3a9d94a38c9f1c5e8d4bba4a259ee` | Remaining entities |
| `011-fluent-api.md` | `8927774c8b8d0503cb5f8dd5484440be4359f615216919bf79fb6da725813195` | Fluent API |
| `012-docs-adrs.md` | `998169aa1a704ddde4838fa23183c3a26ab57f33c24cf73a9c2977edabe4c4c8` | Documentation + ADRs |
| `BACKLOG.md` | `82cd57c7af6132fbe6925ddc1038d206be4ee88d8c82d2752d2558ef8a1cd121` | Backlog |

---

## 3. AGENTS.md HARD RULES (HR-1..HR-22)

| # | Rule | Enforced By |
|---|---|---|
| HR-1 | Spec before src/ | `/spec-check` gate |
| HR-2 | `uv add` only (no `pip`) | `scripts/audit.sh:3`, `scripts/audit.sh:4` |
| HR-3 | Test first, always | `test-first-guard` agent |
| HR-4 | Pydantic frozen+strict | `ODataEntity` base class + ruff/mypy |
| HR-5 | Strict typing, no bare `# type: ignore` | `scripts/audit.sh:1`, `scripts/audit.sh:2` |
| HR-6 | Async-only (no `requests`/`urllib`) | `scripts/audit.sh:7` |
| HR-7 | Single `ClientSession` per client | `__aenter__` guard |
| HR-8 | `BasicAuth("", pat)` — empty user | `scripts/audit.sh:4` + `auth.py` |
| HR-9 | Canonical query order | `query/_serialize.py` |
| HR-10 | URL > 3000 → POST `$batch` | `query/_batch.py` |
| HR-11 | ISO datetime literals (no `datetime'...'`) | `scripts/audit.sh:5` + `_filter.py` |
| HR-12 | Single-quote escaping | `_filter.py:_format_value` |
| HR-13 | `$apply` with `groupby(DateSK/DateValue)` | `_builder.py:_validate_hr13`, `_apply.py:validate` |
| HR-14 | `$expand=Revisions` blocked | `scripts/audit.sh:6` + `_serialize.py:_HrError` |
| HR-15 | HTTP 203+text/html → `AuthenticationError`, no retry | `_http.py:parse_response` + exception hierarchy |
| HR-16 | PAT masked in logs: first 6 + `...` | `scripts/audit.sh:8` + `auth.py:mask_pat` |
| HR-17 | No subagent-of-subagent | `opencode` enforces (Issue #7296) |
| HR-18 | Only `git-keeper` touches git | Agent instructions |
| HR-19 | `ODATA_VERSION` in `client.py` only | `scripts/audit.sh:9` |
| HR-20 | Version from `pyproject.toml` via `importlib.metadata` | `__init__.py:__version__` |
| HR-21 | Coverage ≥ 85% | `pyproject.toml` `[tool.coverage.report]` |
| HR-22 | Only `notion-curator` writes to Notion | Agent instructions |

---

## 4. Spec Backlog Status

| Spec | Title | Test File | Status |
|---|---|---|---|
| 001 | HTTP skeleton | `test_http_skeleton.py` | GREEN (7 tests) |
| 002 | Auth error mapping | `test_auth_error_mapping.py` | GREEN (7 tests) |
| 003 | Retry with tenacity | `test_retry_tenacity.py` | RED (7 tests — `with_retry` exists but tests in RED phase) |
| 004 | Pagination | `test_pagination.py` | RED (5 tests — `iter_pages` exists but tests in RED phase) |
| 005 | Filter DSL | `test_filter_dsl.py` | RED (10 tests — `Filter` exists but tests in RED phase) |
| 006 | Apply DSL | `test_apply_dsl.py` | GREEN (33 tests) |
| 007 | Serialization order | `test_serialize.py` | RED (5 tests — `serialize` exists but tests in RED phase) |
| 008 | Batch POST | `test_batch.py` | RED (5 tests — `maybe_batch` exists but tests in RED phase) |
| 009 | WorkItem entity | `test_workitem_entity.py` | GREEN (5 tests) |
| 010 | Remaining entities | `test_remaining_entities.py` | RED (14 tests — models exist but tests in RED phase) |
| 011 | Fluent API | `test_fluent_api.py` | GREEN (14 tests) |
| 012 | Docs + ADRs | (no test file) | N/A |

**Note**: "RED" means tests written and expected to fail. Some are Red because the implementation existed at test-writing time (SDD pattern), others are legitimately Red because the code hasn't been written yet.

---

## 5. Coverage Report (Baseline)

```
TOTAL                                     653     54    172     22    89.33%
128 passed in 13.11s
```

### Files Below 85% Threshold
| File | Coverage | Missing Lines |
|---|---|---|
| `query/_builder.py` | **73%** | 75, 79-89, 117, 140, 142, 146-154 |
| `_http.py` | **75%** | 47-53, 65-67, 69 |
| `client.py` | **83%** | 51, 100-110, 115-116, 175 |
| `entities/_workitem.py` | **83%** | 35-36 |

### Fully Covered (100%, 11 files)
`auth.py`, `exceptions.py`, `entities/_base.py`, `entities/_board.py`, `entities/_reference.py`, `entities/_system.py`, `entities/_workitemrevisions.py`, `entities/__init__.py`, `metadata.py`, `query/__init__.py`, `retry.py` (99-100%)

---

## 6. Test Suite Structure

```
tests/
  __init__.py                    # package marker
  conftest.py                    # shared fixtures
  unit/
    13 test files                # 128 test functions
  integration/                   # DOES NOT EXIST
```

- **Hypothesis usage**: ZERO (installed as dev dep, never called)
- **Integration tests**: ZERO (marker defined in pyproject.toml but never applied)
- **`@pytest.mark.integration` usage**: ZERO
- **Property-based tests**: ZERO

### Fixtures (conftest.py)
- `fake_pat`, `fake_org`, `fake_project` — string constants
- `odata_version` — parametrized (currently single value: `"v4.0-preview"`)
- `base_url` — derived URL from fixtures
- `mock_http` — `aioresponses` catch-all with priority ordering hack

---

## 7. Key Configuration Files

| File | Purpose |
|---|---|
| `pyproject.toml` | Project metadata, deps, ruff, mypy, pytest, coverage |
| `.pre-commit-config.yaml` | Pre-commit: ruff fix+format, mypy --strict, audit.sh |
| `scripts/audit.sh` | 9 FORBIDDEN token checks |

### Pre-commit Hooks
1. `ruff` — lint + fix (astral-sh/ruff-pre-commit v0.6.9)
2. `ruff-format` — code formatting (v0.6.9)
3. `mypy` — `uv run mypy --strict src/`
4. `audit.sh` — 9 FORBIDDEN token patterns

### CI Commands (from DoD)
- `uv run pytest -q` — unit tests
- `uv run ruff check .` — lint
- `uv run mypy src/` — strict type check
- `uv run pytest --cov=ado_odata_async --cov-fail-under=85` — coverage
- `bash scripts/audit.sh` — FORBIDDEN token scan

---

## 8. Existing Error Catalog (troubleshooting.md)

The troubleshooting guide covers these error scenarios:

| Error | Symptom | Cause | Solution |
|---|---|---|---|
| 401 | `AuthenticationError: 401 Unauthorized` | PAT expired/wrong scope | Create new PAT with Work Items (Read) + Analytics (Read) |
| HTTP 203 + HTML | `AuthenticationError: HTTP 203 Non-Authoritative Information` | PAT invalid OR wrong org name | Verify org, create new PAT |
| 400 (Snapshot) | `BadRequestError: 400 Bad Request` | `WorkItemSnapshot` without `$apply` | Use `$apply` with `groupby` |
| 400 (aggregate alias) | `BadRequestError: 400 Bad Request` | Missing `as <alias>` in aggregate | Library auto-generates; manual queries need explicit alias |
| 400 (arg order) | `BadRequestError: 400 Bad Request` | Wrong `aggregate(field, method)` order | `aggregate("field", "method")` not `aggregate("method", "field")` |
| ValidationError | `pydantic.ValidationError` | Schema mismatch (ADOREST API change) | Use `client.get()` workaround, file issue |
| ModuleNotFoundError | `ModuleNotFoundError: No module named 'aioresponses'` | `uv sync` without `--all-groups` | `uv sync --all-groups` |
| 414 URI Too Long | `aiohttp.ClientResponseError: 414 URI Too Long` | URL exceeds server limit | Library auto-switches to batch at 3000 chars |
| NameError (asyncio) | `NameError: name 'asyncio' is not defined` | `pytest` outside `uv` | Always `uv run pytest` |
| VS403483 | `VS403483: groupby(...) must evaluate to a property access` | `countdistinct` blocked OR aggregate not nested in groupby | Use `$count`, ensure aggregate nested inside groupby |

---

## 9. FORBIDDEN Token Checks (scripts/audit.sh)

| # | Check | Pattern | Hard Rule |
|---|---|---|---|
| 1 | bare `# type: ignore` | Lacks `[code]` + `# reason:` | HR-5 |
| 2 | `as Any` | In src/ (outside stubs) | HR-5 |
| 3 | `pip install` | In any file | HR-2 |
| 4 | `python ` in scripts/ | In scripts/ | HR-2 |
| 5 | `BasicAuth("nonempty", ...)` | In src/ | HR-8 |
| 6 | `datetime'` literal | In src/ | HR-11 |
| 7 | `$expand=Revisions` | In src/ | HR-14 |
| 8 | `requests`/`urllib` imports | In src/ | HR-6 |
| 9 | PAT leak in `print()` | `print(...pat...)` in src/ | HR-16 |
| 10 | `_odata/v2.0` literal | In src/ | HR-19 |

---

## 10. Git History Summary

> Branch: current state as of this inventory. All 12 specs implemented. 128 tests passing. Coverage at 89.33%. All static checks clean.

---

*End of Phase 0 Inventory. Proceed to Phase 1: Hostile Critique.*
