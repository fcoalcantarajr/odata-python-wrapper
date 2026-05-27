<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# SR-003: Honor Retry-After header on 429 responses

- id: SR-003
- slug: retry-after-429
- status: DRAFT
- created: 2026-05-27
- owner: sisyphus
- findings-addressed: SR-003, SR-016

## User Story

As a developer using this client in a rate-limited Azure DevOps environment,
I want the retry mechanism to honor the `Retry-After` header from 429 responses,
so that the client respects server backpressure instead of burning through retry
budget with exponential jitter that's shorter than the server's requested wait.

## Use Cases

- UC1: 429 response with `Retry-After: 60` → retry after at least 60s (not 0.5s exponential jitter)
- UC2: 429 response without `Retry-After` → fall back to exponential jitter
- UC3: Non-rate-limit `TransientError` (5xx) → unaffected, uses existing exponential jitter
- UC4: RateLimitError cap logic is simplified (SR-016 folded in)

## Acceptance Criteria (Gherkin absoluto)

### AC-1: RateLimitError stores retry_after attribute

```
Given RateLimitError is imported from ado_odata_async.exceptions
When a RateLimitError is raised with message and retry_after=60.0
Then exc.retry_after == 60.0
  And str(exc) contains "Rate limit"
```

### AC-2: Custom wait function reads retry_after from RateLimitError

```
Given a retry state where the outcome is a RateLimitError with retry_after=60.0
When the custom wait function is called
Then the returned wait time >= 60.0
```

### AC-3: Custom wait function falls back to exponential jitter for non-retry-after errors

```
Given a retry state where the outcome is a generic TransientError
When the custom wait function is called
Then the returned wait time is between 0.5 and 10.0 seconds
  And over 1000 samples the distribution is consistent with exponential backoff (verified via Hypothesis @given)
```

### AC-4: Retry-After from header is passed through

```
Given parse_response receives an HTTP 429 with Retry-After: 30
When parse_response executes
Then it raises RateLimitError with retry_after == 30.0
```

### AC-5: RateLimitError without retry_after still retries with exponential jitter

```
Given RateLimitError is raised without specifying retry_after
Then exc.retry_after is None
  And the wait function returns a value between 0.5 and 10.0 seconds
```

### AC-6: _stop does not stop early on non-RateLimit TransientError

```
Given max_attempts=5
  And _stop is called with a generic TransientError at attempt 3
When _stop evaluates
Then _stop returns False (does not stop, continues retrying)
```

## NFRs

- **Performance:** Custom wait function must complete in < 1µs (pure computation, no I/O)
- **Observability:** `before_sleep_log` still fires; log message includes retry_after value when present

## INVEST self-score

- **I**ndependent: 9/10 — standalone change, no dependency on other specs
- **N**egotiable: 8/10 — exact retry_after buffer value (0.5s) is negotiable
- **V**aluable: 10/10 — without this, rate-limited environments are unusable
- **E**stimable: 9/10 — clear scope, 3 files to modify
- **S**mall: 8/10 — fits in 1-2 implementation sessions
- **T**estable: 9/10 — AC-3 and AC-6 tightened for precision; Hypothesis property test needed for distribution

Média: 8.8/10

## Out-of-scope

- Retry-After with HTTP-date format (RFC 7231 §7.1.3) — ADO always uses seconds
- Modifying stop logic for non-RateLimitError paths

## Test plan

- AC-1 → `tests/unit/test_sr_003_retry_after.py::test_ac1_rate_limit_error_stores_retry_after`
- AC-2 → `tests/unit/test_sr_003_retry_after.py::test_ac2_wait_fn_reads_retry_after`
- AC-3 → `tests/unit/test_sr_003_retry_after.py::test_ac3_wait_fn_fallback_jitter`
- AC-4 → `tests/unit/test_sr_003_retry_after.py::test_ac4_parse_response_passes_retry_after`
- AC-5 → `tests/unit/test_sr_003_retry_after.py::test_ac5_no_retry_after_fallback`
- AC-6 → `tests/unit/test_sr_003_retry_after.py::test_ac6_stop_logic_simplified`

## Hard Rules

- HR-15 (retryable exceptions — RateLimitError remains a TransientError subclass)
