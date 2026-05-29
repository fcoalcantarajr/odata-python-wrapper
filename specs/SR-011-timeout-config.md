<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# SR-011: Client timeout configuration

- id: SR-011
- slug: timeout-config
- status: APPROVED
- created: 2026-05-27
- owner: sisyphus
- findings-addressed: SR-011

## User Story

As a developer using this client in a latency-sensitive environment,
I want to configure request timeouts when creating an `AdoODataClient`,
so that I can fail fast when Azure DevOps is slow instead of waiting for
the default 5-minute aiohttp timeout.

## Use Cases

- UC1: `AdoODataClient(org, project, pat, timeout=ClientTimeout(total=30))` uses 30s total timeout
- UC2: `AdoODataClient(org, project, pat)` without timeout uses sensible default (30s total, 10s connect)
- UC3: The timeout is passed to `aiohttp.ClientSession` constructor
- UC4: The timeout can be inspected after construction

## Acceptance Criteria (Gherkin absoluto)

### AC-1: ClientSession receives timeout parameter

```
Given AdoODataClient is created with timeout=aiohttp.ClientTimeout(total=30)
When __aenter__ executes
Then self._session is created with timeout.total == 30
```

### AC-2: Default timeout is applied when none provided

```
Given AdoODataClient is created without timeout argument
When __aenter__ executes
Then self._session is created with timeout.total == 30
  And self._session is created with timeout.connect == 10
```

### AC-3: Timeout is available as an attribute

```
Given client = AdoODataClient(org="o", project="p", pat="x")
When client is entered
Then hasattr(client, "timeout") is True (or equivalent public/private access)
```

### AC-4: Backward compatible — existing keyword-only args still work

```
Given AdoODataClient is created with only org, project, pat, batch_threshold
When __aenter__ executes
Then no error is raised
  And default timeout is used
```

## NFRs

- **Backward compatibility:** All existing code using `AdoODataClient(...)` must work unchanged
- **Type safety:** `timeout` parameter must accept `aiohttp.ClientTimeout | None`

## INVEST self-score

- **I**ndependent: 10/10 — standalone change, one file
- **N**egotiable: 8/10 — exact default values (60/30 vs 30/10) are negotiable
- **V**aluable: 9/10 — production requirement for timeout configurability
- **E**stimable: 9/10 — 10 lines of code, clear contract
- **S**mall: 10/10 — < 10 lines changed
- **T**estable: 10/10 — mock ClientSession creation, verify constructor args

Média: 9.3/10

## Out-of-scope

- Per-request timeout (aiohttp.ClientSession timeout applies to all requests on that session)
- Dynamic timeout adjustment after session creation
- Timeout for batch POST requests specifically

## Test plan

- AC-1 → `tests/unit/test_sr_011_timeout.py::test_ac1_custom_timeout_passed`
- AC-2 → `tests/unit/test_sr_011_timeout.py::test_ac2_default_timeout_applied`
- AC-3 → `tests/unit/test_sr_011_timeout.py::test_ac3_timeout_attribute_exists`
- AC-4 → `tests/unit/test_sr_011_timeout.py::test_ac4_backward_compatible`

## Hard Rules

- HR-6 (async-only — timeout applies to aiohttp, not requests)
- HR-7 (single ClientSession — timeout is set at creation)
