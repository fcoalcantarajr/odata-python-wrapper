# Anti-Slop Inventory — `ado_odata_async`

> **Phase 0**: INGEST — Full codebase baseline for hostile AI-archaeology audit.
> **Date**: 2026-05-27T22:52:30Z
> **Reviewer**: 35-year Python veteran (Python 1.0 in 1994, production aiohttp, ADO OData since 2018)

---

## 1. Source Package: Every Public Symbol with SHA256

### 1.1 File Index (21 `.py` files, 666 executable statements)

| # | File | SHA256 | Stmts | Coverage |
|---|------|--------|-------|----------|
| 1 | `__init__.py` | `117086422622dba84b9d17c0dab942b94a69c81aed918612406d21de3f0786d5` | 12 | 100% |
| 2 | `_http.py` | `9244e06cb4ca748746d0566bef863a39c7952d4f73d561b3de7f88fd8458b064` | 44 | **63%** |
| 3 | `auth.py` | `bae0acb461ff9439cd5ae255d8c8fa16bf0b0234d2fd30339787785037aaa246` | 6 | 100% |
| 4 | `client.py` | `7cd8ddd77e4ab9fae3997357bd1b09facc857a0ed5ead36143b296059a5802cd` | 78 | **84%** |
| 5 | `exceptions.py` | `8fec9bb4a7813e276ea69387e88d35f9b2d442dba2634e4c4665339ad5f3abb6` | 16 | 100% |
| 6 | `metadata.py` | `e7373cc2a3bc86deaec98971a30aa4cd47b5004a3789fb239063b8a293953fb6` | 5 | 100% |
| 7 | `pagination.py` | `74cd9d75a24d3a537cdbee1858fa1265e5b8dc44186d2c5140c1556a5d088983` | 37 | **90%** |
| 8 | `retry.py` | `9fb4319562b4759222a890e03dc48aa5a97e71773008cf040d825b5163d27ab2` | 38 | **96%** |
| 9 | `query/__init__.py` | `25a328d4a473ae2a8532f9c395c10635234e6cf639aebc6f2da377ce9ce06719` | 5 | 100% |
| 10 | `query/_apply.py` | `067ac26eebd46478d27cf12eaf620469a93e6401ac4155e5664f3f938df28802` | 106 | **99%** |
| 11 | `query/_batch.py` | `f751b565a98c1b7a692223f95f9e056303321e04b30290740878582ff7e0f1f7` | 29 | **85%** |
| 12 | `query/_builder.py` | `ba320a174e2edf34788c7813fd3b2319b825c1cbd83d503719550b99198818bd` | 77 | **98%** |
| 13 | `query/_filter.py` | `3bf87ce950f51bc1be413dc6050d27d67ccfac6b840278c579795140daa11a77` | 78 | **89%** |
| 14 | `query/_serialize.py` | `5f45d9db495eaaaf1c0c3474b2b57de74f1f852ee699a3d1a8f7396e2f41a2df` | 26 | **92%** |
| 15 | `entities/__init__.py` | `2b2204a81b03e2a0f1c93ebc76af21328334c2b045a4355b6b7b4b9968132ecf` | 6 | 100% |
| 16 | `entities/_base.py` | `953066f5aab2c903aea89e83e406b54a06c33fdbcd1a900801545e6dba825101` | 11 | 100% |
| 17 | `entities/_board.py` | `baa85a8a54e92fbdc71f7bbd6e60d1bf0883b68dd1550fdab8a853fefd57a26e` | 9 | 100% |
| 18 | `entities/_reference.py` | `25e7eea68f8a247cf8fc63fd26943a2186d62717c9f4f61ef64993b7d347cba2` | 13 | 100% |
| 19 | `entities/_system.py` | `37799d5d24514f7552962f390787786de341093e8988f7c6d496563ccb6fcbad` | 16 | 100% |
| 20 | `entities/_workitem.py` | `5d974cc6fda740ffdafbc918b3932a3cec003a54023e512fa6bd622f0558d4e4` | 16 | **83%** |
| 21 | `entities/_workitemrevisions.py` | `b01df4cc68843674a2b51f10b2af6686718893406fb3ac06f2f0cbf726786cfe` | 8 | 100% |

**Coverage trend**: 89.33% (prior senior audit) → **91.57% now** (146 tests). Improvement from the SR-* fix cycle.

**Files below 85% threshold** (NEW after prior fix cycle): `_http.py` at **63%** — was 75% before. This is a regression. Likely because new code paths (batch error handling, 203 edge cases) were added without tests.

### 1.2 Public Symbols by Module

#### Core (`auth.py`, `_http.py`, `retry.py`, `pagination.py`)
| Module | Symbol | Line | Kind |
|--------|--------|------|------|
| `auth.py` | `build_basic_auth` | 8 | `BasicAuth("", pat)` — HR-8 |
| `auth.py` | `mask_pat` | 12 | `pat[:6] + "..."` |
| `_http.py` | `parse_response` | 20 | async fn — HTTP status → typed exception |
| `retry.py` | `with_retry` | 72 | deco — tenacity on TransientError |
| `retry.py` | `T` | 21 | TypeVar |
| `pagination.py` | `iter_pages` | 17 | async generator — `$skip`/`$top` + `@odata.nextLink` |

#### Client (`client.py`)
| Symbol | Line | Kind |
|--------|------|------|
| `ODATA_VERSION` | 30 | constant: `"v4.0-preview"` (HR-19) |
| `AdoODataClient` | 33 | async context manager class |
| `AdoODataClient.__init__` | 40 | `(*, org, project, pat, batch_threshold=3000)` |
| `AdoODataClient.__aenter__` | 49 | returns `Self` |
| `AdoODataClient.__aexit__` | 66 | closes session |
| `AdoODataClient.__repr__` | 79 | masked PAT |
| `AdoODataClient.get` | 87 | async — `(entity_set, **params) -> dict` |
| `AdoODataClient.get_workitem` | 122 | async — `(id_) -> WorkItem` |
| `AdoODataClient.paginate` | 144 | `(entity_set, *, top, query) -> AsyncIterator` |
| `AdoODataClient.query` | 168 | `(entity_set) -> QueryBuilder` |

#### Exceptions (`exceptions.py`)
| Symbol | Line | Bases | Notes |
|--------|------|-------|-------|
| `AdoODataError` | 6 | `Exception` | Base |
| `AuthenticationError` | 10 | `AdoODataError` | NEVER retry (HR-15) |
| `BadRequestError` | 14 | `AdoODataError` | NOT retryable |
| `TransientError` | 18 | `AdoODataError` | Retryable by tenacity |
| `RateLimitError` | 22 | `TransientError` | Has `retry_after` attribute |

#### Query DSL (5 files)
| Module | Symbol | Line | Kind |
|--------|--------|------|------|
| `query/__init__.py` | `Apply`, `Filter`, `QueryBuilder`, `maybe_batch`, `parse_batch_response`, `serialize` | — | re-exports |
| `query/_apply.py` | `Apply` | 21 | class — fluent `$apply` builder |
| `query/_apply.py` | `Apply.__init__` | 45 | `(entity_type=None)` |
| `query/_apply.py` | `Apply.groupby` | 60 | dual-role shortcut+mutator |
| `query/_apply.py` | `Apply.filter` | 94 | dual-role |
| `query/_apply.py` | `Apply.aggregate` | 107 | dual-role, blocks countdistinct |
| `query/_apply.py` | `Apply.validate` | 175 | HR-13 enforcement |
| `query/_apply.py` | `Apply.build` | 193 | serialize to `$apply=...` |
| `query/_apply.py` | `Apply.__str__` | 244 | alias for build() |
| `query/_batch.py` | `maybe_batch` | 23 | URL > 3000 → POST `$batch` |
| `query/_batch.py` | `build_batch_get_body` | 61 | multipart body |
| `query/_batch.py` | `parse_batch_response` | 97 | multipart → JSON |
| `query/_builder.py` | `QueryBuilder` | 28 | class — immutable fluent builder |
| `query/_builder.py` | `QueryBuilder.__init__` | 35 | `(client=None, entity_set="")` |
| `query/_builder.py` | `QueryBuilder.__str__` | 58 | serialized with HR-9 |
| `query/_builder.py` | `QueryBuilder.__repr__` | 62 | debug |
| `query/_builder.py` | `QueryBuilder.apply` | 70 | chainable |
| `query/_builder.py` | `QueryBuilder.filter` | 82 | chainable |
| `query/_builder.py` | `QueryBuilder.orderby` | 88 | chainable |
| `query/_builder.py` | `QueryBuilder.expand` | 94 | chainable |
| `query/_builder.py` | `QueryBuilder.select` | 100 | chainable |
| `query/_builder.py` | `QueryBuilder.skip` | 110 | chainable |
| `query/_builder.py` | `QueryBuilder.top` | 116 | chainable |
| `query/_builder.py` | `QueryBuilder.get` | 133 | async — terminal |
| `query/_builder.py` | `QueryBuilder.paginate` | 146 | terminal — async iterator |
| `query/_filter.py` | `Filter` | 33 | class — expression tree |
| `query/_filter.py` | `Filter.eq` | 104 | static factory |
| `query/_filter.py` | `Filter.ne` | 109 | static factory |
| `query/_filter.py` | `Filter.gt` | 114 | static factory |
| `query/_filter.py` | `Filter.ge` | 119 | static factory |
| `query/_filter.py` | `Filter.lt` | 124 | static factory |
| `query/_filter.py` | `Filter.le` | 129 | static factory |
| `query/_filter.py` | `Filter.and_` | 138 | static factory |
| `query/_filter.py` | `Filter.or_` | 143 | static factory |
| `query/_filter.py` | `Filter.not_` | 148 | static factory |
| `query/_filter.py` | `Filter.contains` | 157 | static factory |
| `query/_filter.py` | `Filter.build` | 165 | serialize tree to string |
| `query/_serialize.py` | `CANONICAL_ORDER` | 16 | list of 7 option names |
| `query/_serialize.py` | `serialize` | 31 | dict → URL-encoded query string |

#### Entities (7 files)
| Module | Symbol | Line | Kind |
|--------|--------|------|------|
| `entities/_base.py` | `ODataEntity` | 10 | Base — frozen+strict+extra=forbid |
| `entities/_board.py` | `WorkItemBoardSnapshot` | 15 | class |
| `entities/_board.py` | `WorkItemBoardSnapshotWithDescription` | 34 | class |
| `entities/_reference.py` | `Iteration` | 12 | class |
| `entities/_reference.py` | `Project` | 22 | class |
| `entities/_reference.py` | `Team` | 31 | class |
| `entities/_reference.py` | `Area` | 40 | class |
| `entities/_system.py` | `Date` | 14 | class |
| `entities/_system.py` | `User` | 29 | class |
| `entities/_system.py` | `WorkItemType` | 38 | class |
| `entities/_system.py` | `WorkItemLink` | 46 | class |
| `entities/_workitem.py` | `WORK_ITEM_TYPES` | 11 | tuple constant |
| `entities/_workitem.py` | `WorkItem` | 20 | class — with redundant validator |
| `entities/_workitemrevisions.py` | `WorkItemRevisions` | 14 | class |

#### Deferred
| Module | Symbol | Line | Kind |
|--------|------|------|------|
| `metadata.py` | `fetch_metadata` | 8 | stub — raises `NotImplementedError` |

---

## 2. Documentation Files (SHA256)

### 2.1 Root
| File | SHA256 | Lines |
|------|--------|-------|
| `AGENTS.md` | `38e726f2aeb8ff9f3b4ac7fda899a1fb9a16b2ff8d498b66fa09d703be49f15c` | 142 |
| `README.md` | `1e2a6515d0d112a2bf23d7220f921fef1a5e831f3efb6434491886bcec864e99` | — |

### 2.2 `docs/`
| File | SHA256 | Changed since prior audit? |
|------|--------|---------------------------|
| `getting-started.md` | `63e4c1cbd7a32a833726460bdf0e9b8913027a2d64147943babe8e2c41224b41` | No |
| `concepts.md` | `8da3b4506639d0b394bb57be84d4bfd71c8b5f59659c39259934d98b481b69de` | No |
| `cookbook.md` | `6df0c977232ee82dae49c5cba492d6140d07fb2671ab44d9666f23e3391641ac` | **YES** (was `c1486ec2`) |
| `troubleshooting.md` | `eff8f8ba16fde6b8fb37e492cd03363a12749b7bf1ca0b9147ac822605f5a54a` | No |
| `glossary.md` | `6593b452ecc74c57ae3e0eaecd9440ca52f2d04f3288b9aedf7e87edfda7b908` | No |
| `decisions.md` | `631a5b28636745411e2f193cf43b7b22943a1efebad4a9001297972cc69ef3cb` | No |
| `architecture.md` | `5c8333004e5f61ffce28b0e1f9ab1656349a3a7fbedcd388b6429c41c88599c3` | No |
| `HANDOFF.md` | `ee9db7761d414b2bff3ae3b9357338d66f74e0268a6a36e889e00fdd8848e4b7` | No |

**Note**: `cookbook.md` SHA256 changed — the prior SR-005 fix (docs alignment) modified it. Verify content.

### 2.3 `docs/_review/` (prior audit artifacts)
| File | SHA256 | Description |
|------|--------|-------------|
| `senior_audit_inventory.md` | (prior) | Phase 0 inventory from first audit |
| `senior_audit_findings.md` | (prior) | 18 findings (SR-001..SR-018) B1-B8 |
| `senior_audit_plan.md` | (prior) | Implementation plan for SR-* fixes |
| `senior_final.md` | (prior) | Final report after SR-* fix cycle |
| `senior_findings.md` | (prior) | Alternate findings version |
| `senior_inventory.md` | (prior) | Alternate inventory version |

### 2.4 Spec Files (`specs/`)
| File | SHA256 | Title |
|------|--------|-------|
| `000-TEMPLATE.md` | `8a6bb8512e6df588c169a0585b40bcf03b35db7c35015dfdc8bf075f0ffa84a2` | Template |
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
| `012-docs-adrs.md` | `998169aa1a704ddde4838fa23183c3a26ab57f33c24cf73a9c2977edabe4c4c8` | Docs + ADRs |
| `BACKLOG.md` | `82cd57c7af6132fbe6925ddc1038d206be4ee88d8c82d2752d2558ef8a1cd121` | Backlog |

### 2.5 SR-* Spec Files (from prior fix cycle)
| File | SHA256 | Title |
|------|--------|-------|
| `SR-002-code-cleanup.md` | `a183df746dca16809e63221554d5a6a379e029d00801d2a86b71c3417d909611` | Code cleanup |
| `SR-003-retry-after-429.md` | `33081bdeb5260c0dd9e06bce2019daba56d8dec44970975db60198958a686e15` | Retry-After for 429 |
| `SR-004-hr13-dedup.md` | `0a890b8e6282e26f783b75bb7771fd740d9407d1a3ce87273e7e3b7eb326faf0` | HR-13 dedup |
| `SR-005-integration-test.md` | `3569c10b4537cd5a4cc960ca544d7506f0b05b2a525c8f78c468c36eee55bc6a` | Integration test |
| `SR-006-hypothesis-tests.md` | `f15a22db4db763a95f1800133abf6716517f5558f7a04a10745ef7ff3eebfdf7` | Hypothesis tests |
| `SR-007-mock-fixture.md` | `e41c29741da6e0de69e10772ee8fde389040fd80d421e7414c182454ab4b120d` | Mock fixture |
| `SR-010-docs-cleanup.md` | `ba79f7bd758ad6e0b2a304742d21c3c0c78c84413a319a5bb6fa2e8891b3d7ce` | Docs cleanup |
| `SR-011-timeout-config.md` | `9cac2377acbeecf33ef9a513e6f6cbc5496024b1f01666d44d3f066f8c3e526c` | Timeout config |
| `SR-013-error-coverage.md` | `40671fa744f4cc14a314b956ae3c4a8c9effa98dc2da0611072707fb2ebb648d` | Error coverage |
| `SR-015-misc-trivial.md` | `f61fd32280747278401cebfd192829c84b13f3084bdbdd4f8a7d072db387f133` | Misc trivial |

---

## 3. AGENTS.md HARD RULES (HR-1..HR-22)

| # | Rule | Enforced By | Prior Audit Status |
|---|------|-------------|-------------------|
| HR-1 | Spec before src/ | `/spec-check` gate | OK |
| HR-2 | `uv add` only (no `pip`) | `audit.sh:3`,`:4` | OK |
| HR-3 | Test first, always | `test-first-guard` agent | OK |
| HR-4 | Pydantic frozen+strict | `ODataEntity` base + ruff/mypy | OK |
| HR-5 | Strict typing, no bare `# type: ignore` | `audit.sh:1`,`:2` | OK |
| HR-6 | Async-only (no `requests`/`urllib`) | `audit.sh:7` | OK |
| HR-7 | Single `ClientSession` per client | `__aenter__` guard | OK |
| HR-8 | `BasicAuth("", pat)` — empty user | `audit.sh:4` + `auth.py` | OK |
| HR-9 | Canonical query order | `query/_serialize.py` | OK |
| HR-10 | URL > 3000 → POST `$batch` | `query/_batch.py` | OK |
| HR-11 | ISO datetime (no `datetime'...'`) | `audit.sh:5` + `_filter.py` | OK |
| HR-12 | Single-quote escaping | `_filter.py:_format_value` | OK |
| HR-13 | Snapshot `$apply` groupby | `_apply.py:_check_snapshot_groupby` | OK (deduped) |
| HR-14 | `$expand=Revisions` blocked | `audit.sh:6` + `_serialize.py` | OK |
| HR-15 | HTTP 203 → `AuthenticationError`, no retry | `_http.py` + exception hierarchy | OK |
| HR-16 | PAT masked in logs | `audit.sh:8` + `mask_pat` | OK |
| HR-17 | No subagent-of-subagent | opencode enforces | OK |
| HR-18 | Only `git-keeper` touches git | Agent instructions | OK |
| HR-19 | `ODATA_VERSION` in `client.py` only | `audit.sh:9` | OK |
| HR-20 | Version from `pyproject.toml` via `importlib.metadata` | `__init__.py:__version__` | OK |
| HR-21 | Coverage ≥ 85% | `pyproject.toml` | OK (91.57%) |
| HR-22 | Only `notion-curator` writes to Notion | Agent instructions | OK |

**B10 audit needed**: Each HR must be verified against Tier 1/2 sources. The prior audit accepted these as-is. B10 will do trust-ladder verification.

---

## 4. Spec Backlog Status

| Spec | Title | Test File | Tests | Status |
|------|-------|-----------|-------|--------|
| 001 | HTTP skeleton | `test_http_skeleton.py` | 7 | GREEN |
| 002 | Auth error mapping | `test_auth_error_mapping.py` | 7 | GREEN |
| 003 | Retry with tenacity | `test_retry_tenacity.py` | 7 | GREEN |
| 004 | Pagination | `test_pagination.py` | 5 | GREEN |
| 005 | Filter DSL | `test_filter_dsl.py` | 10 | GREEN |
| 006 | Apply DSL | `test_apply_dsl.py` | 33 | GREEN |
| 007 | Serialization order | `test_serialize.py` | 5 | GREEN |
| 008 | Batch POST | `test_batch.py` | 5 | GREEN |
| 009 | WorkItem entity | `test_workitem_entity.py` | 5 | GREEN |
| 010 | Remaining entities | `test_remaining_entities.py` | 14 | GREEN |
| 011 | Fluent API | `test_fluent_api.py` | 14 | GREEN |
| 012 | Docs + ADRs | (no test file) | N/A | N/A |
| **Total** | | **13 test files** | **146** | **ALL GREEN** |

**Status change from prior audit**: Previously 7 specs were "RED" (tests expected to fail). All now pass. This is the result of the SR-* fix cycle that shipped fixes for SR-001 through SR-015+. The RED-phase docstrings are still lying (stale "RED phase" headers on passing tests).

**SR-* backlog after prior fix cycle**:
- SR-001 (session guard): ✅ Fixed — `pagination.py:42-44` now has RuntimeError guard
- SR-002 (redundant validator): ❌ Still open — `_workitem.py:31-37` validator still present
- SR-003 (Retry-After): ✅ Fixed — `retry.py:38-39` reads retry_after; `_http.py:62-64` stores it
- SR-004 (HR-13 dedup): ✅ Fixed — `_apply.py:249` shared `_check_snapshot_groupby`
- SR-005 (integration tests): ❌ Still open — no integration tests, cookbook still claims testing
- SR-006 (Hypothesis): ❌ Still open — Hypothesis never used in tests
- SR-007 (mock fixture): ❌ Still open — aioresponses monkey-patch still in conftest.py
- SR-008 (__setattr__): ❌ Still open — catches ValidationError not FrozenInstanceError
- SR-009 (double filter): ❌ Still open — pagination.py still rebuilds dict
- SR-010 (dead import): ❌ Still open — `getting-started.md` still imports unused Filter
- SR-011 (timeout config): ❌ Still open — no ClientTimeout parameter
- SR-012 (serialize reads original query): ❌ Still open — `_serialize.py:58` reads `query` not `filtered`
- SR-013 (error coverage): ❌ Still open — _http.py 63% coverage
- SR-014 (stale docstrings): ❌ Still open — RED-phase headers on passing tests
- SR-015 (SR-001 test): ✅ Fixed — test now passes with RuntimeError guard
- SR-016 (rate limit cap): ✅ Fixed — stop logic now properly ordered
- SR-017 (missing __all__): ❌ Still open
- SR-018 (Spec 012 AC): ❌ Still open

**Status**: 5 of 18 SR-* findings fixed in prior cycle; 13 remain open.

---

## 5. Coverage Report (Current)

```
Name                                        Stmts   Miss Branch BrPart  Cover   Missing
---------------------------------------------------------------------------------------
src/ado_odata_async/_http.py                   44     14     16      4    63%   47-53, 56->68, 60-61, 68->71, 69, 72-74, 76, 78
src/ado_odata_async/client.py                  78     11     14      2    84%   51, 103-113, 118-120, 179
src/ado_odata_async/entities/_workitem.py      16      2      2      1    83%   35-36
src/ado_odata_async/pagination.py              37      3     14      2    90%   43-44, 52
src/ado_odata_async/query/_apply.py           106      0     52      1    99%   231->240
src/ado_odata_async/query/_batch.py            29      2     12      4    85%   136, 137->133, 140->133, 143
src/ado_odata_async/query/_builder.py          77      1     10      1    98%   104
src/ado_odata_async/query/_filter.py           78      7     20      4    89%   88, 90, 97, 121, 126, 131, 186
src/ado_odata_async/query/_serialize.py        26      2     12      1    92%   63-64
src/ado_odata_async/retry.py                   38      0     12      2    96%   36->41, 63->67
---------------------------------------------------------------------------------------
TOTAL                                         666     42    164     22    92%

146 passed in 20.09s  |  Required: 85%  |  Current: **91.57%**
```

**Key regressions**: `_http.py` dropped from 75% to **63%** — the batch error handling paths added in the SR-* cycle are untested.

---

## 6. Test Suite Structure

```
tests/
  __init__.py                    # package marker
  conftest.py                    # shared fixtures (mock_http with monkey-patch)
  unit/
    13 test files                # 146 test functions (ALL PASSING)
  integration/                   # DOES NOT EXIST
```

### Fixture Status
- `fake_pat`, `fake_org`, `fake_project` — string constants
- `odata_version` — parametrized (single value: `"v4.0-preview"`)
- `base_url` — derived URL
- `mock_http` — aioresponses with **monkey-patch catch-all** (SR-007 open)
- `@pytest.mark.integration`: **never used** (SR-005 open)
- `@given` / `hypothesis`: **never imported** (SR-006 open)

---

## 7. Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata, deps, ruff, mypy, pytest, coverage |
| `.pre-commit-config.yaml` | 4 hooks: ruff fix, ruff format, mypy --strict, audit.sh |
| `scripts/audit.sh` | 9 FORBIDDEN token checks via `rg` |

### Pre-commit Hooks
1. `ruff` — lint + fix (v0.6.9)
2. `ruff-format` — code formatting (v0.6.9)
3. `mypy` — `uv run mypy --strict src/`
4. `audit.sh` — 9 FORBIDDEN token patterns

---

## 8. Error Catalog (troubleshooting.md)

| Error | Symptom | Cause | Solution |
|-------|---------|-------|----------|
| 401 | `AuthenticationError: 401 Unauthorized` | PAT expired/wrong scope | Create new PAT |
| HTTP 203 + HTML | `AuthenticationError: HTTP 203` | PAT invalid OR wrong org name | Verify org, new PAT |
| 400 (Snapshot) | `BadRequestError: 400` | Snapshot no `$apply` | Use `groupby` |
| 400 (alias) | `BadRequestError: 400` | Missing `as <alias>` in aggregate | Library auto-generates |
| 400 (arg order) | `BadRequestError: 400` | Wrong `aggregate(field, method)` order | Correct order |
| ValidationError | `pydantic.ValidationError` | Schema mismatch | Use `client.get()` workaround |
| ModuleNotFoundError | No module 'aioresponses' | `uv sync` without `--all-groups` | `uv sync --all-groups` |
| 414 URI Too Long | `aiohttp.ClientResponseError: 414` | URL > server limit | Auto-batch at 3000 |
| NameError (asyncio) | `NameError: name 'asyncio'` | pytest outside uv | `uv run pytest` |
| VS403483 | groupby must be property access | `countdistinct` blocked | Use `$count` |

---

## 9. FORBIDDEN Token Checks (scripts/audit.sh)

| # | Check | Pattern | Hard Rule |
|---|-------|---------|-----------|
| 1 | bare `# type: ignore` | Lacks `[code]` + `# reason:` | HR-5 |
| 2 | `as Any` | In src/ | HR-5 |
| 3 | `pip install` | Any file | HR-2 |
| 4 | `python ` in scripts/ | scripts/ | HR-2 |
| 5 | `BasicAuth("nonempty", ...)` | src/ | HR-8 |
| 6 | `datetime'` literal | src/ | HR-11 |
| 7 | `$expand=Revisions` | src/ | HR-14 |
| 8 | `requests`/`urllib` imports | src/ | HR-6 |
| 9 | PAT leak in `print()` | `print(...pat...)` in src/ | HR-16 |
| 10 | `_odata/v2.0` literal | src/ | HR-19 |

**B10 check needed**: Verify each audit.sh check actually matches its declared HR. For example, check 2 (`as Any`) may produce false positives for legitimate `as Any` in type-coercion patterns.

---

## 10. Git Log — Last 90 Days

**Single author**: `omo-agent` (100% of commits — this is an AI-generated project)

### Commits with AI-scented messages

| Commit | Message | AI Indicators |
|--------|---------|---------------|
| `2ac54b4` | `feat: initialize ado-odata-async project with async client for Azure DevOps Analytics OData` | Overly long, marketing-speak |
| `68adf4c` | `chore(scaffold): complete Step 7 esqueleto + pre-commit hardening` | "esqueleto" — bilingual |
| `4c758f3` | `fix(agents,config): migrate permission schema to enum + canonical $schema URLs` | Technical but verbose |
| `3d751d1` | `feat(http): single ClientSession + v4.0-preview + empty-user BasicAuth` | Descriptive, feature-pack |
| `8b90566` | `feat: implement real-world Azure DevOps authentication, resolve all oracle feedback, and pass verification` | Marketing: "real-world" |
| `657c40b` | `demo: real-data flow metrics from ADO Analytics OData` | "real-data" marketing |
| `d95c7d2` | `docs: intern-friendly guide in PT-BR for flow metrics` | Unnecessarily long for what it is |
| `1691df0` | `Merge F12: nest groupby+aggregate + block countdistinct` | Opaque scope reference "F12" |
| `934df54` | `docs(audit): add senior final report (Phase 2 complete) omo-agent` | Self-referential |

**Note**: The entire git history is AI-generated, which is expected for a project built via opencode. The audit should focus on the code quality consequences, not the origin.

### Commit Summary (50 commits total)
- **feat**: 14 — feature commits
- **fix**: 12 — fixes
- **refactor**: 2 — refactoring
- **docs**: 8 — documentation
- **chore**: 7 — config/chores
- **test**: 1 — test changes
- **config**: 3 — agent configuration
- **demo**: 1 — demo script
- **Merge**: 2 — merge commits

### Prior SR-* Fix Cycle (from prior audit fix implementation)
The SR-* fix cycle shipped these changes:
- SR-001 ✅: Added session-None guard in `pagination.py:42-44`
- SR-003 ✅: Added `retry_after` to `RateLimitError`, `_make_wait` respects it
- SR-004 ✅: Extracted `_check_snapshot_groupby` in `_apply.py:249`
- SR-015 ✅: SR-001 test now passes
- SR-016 ✅: Stop logic fixed

---

## 11. Prior Audit Artifacts

The prior hostile audit (also by Sisyphus) produced:
- `docs/_review/senior_audit_inventory.md` — Phase 0 inventory
- `docs/_review/senior_audit_findings.md` — 18 findings (SR-001..SR-018) across B1-B8
- `docs/_review/senior_audit_plan.md` — Implementation plan
- `docs/_review/senior_final.md` — Final report

**This audit extends with B9 (AI-archaeology fingerprints F1-F13) and B10 (AI-context audit) buckets**, which the prior audit did not cover.

---

## 12. Summary Statistics

| Metric | Value | vs Prior Audit |
|--------|-------|----------------|
| Source files | 21 | Same |
| Executable statements | 666 | +13 |
| Public classes | 18 | Same |
| Public functions | 7 | Same |
| Public methods | 43 | Same |
| Tests | 146 passing | +18 |
| Coverage | **91.57%** | +2.24pp |
| _http.py coverage | **63%** | **-12pp** (regression) |
| Specs complete | 12/12 main + 10 SR-* | +10 |
| Integration tests | 0 | Same |
| Hypothesis tests | 0 | Same |
| Lint + mypy + audit | All clean | Same |
| Pre-commit hooks | 4 | Same |

---

*End of Phase 0 Inventory. Proceed to Phase 1: Hostile Critique (B9 + B10 buckets).*
