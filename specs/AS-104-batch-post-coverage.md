<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# AS-104 — Add unit test coverage for batch POST path and ClientError handler

- id: AS-104
- slug: batch-post-coverage
- status: APPROVED
- created: 2026-05-28
- owner: sisyphus
- findings-addressed: AS-104

## User Story

As a developer maintaining the HTTP layer,
I want the batch POST code path (URL > 3000 chars) and the ClientError handler to be covered by unit tests,
so that regressions in error handling and batch behavior are caught automatically.

## Use Cases

- UC1: Build URL > 3000 chars → mock POST returning 400 → call `client.get()` → verify `BadRequestError` propagates
- UC2: Build URL > 3000 chars → mock `session.post()` raising `aiohttp.ClientError` → call `client.get()` → verify `TransientError` with chained cause
- UC3: Build URL > 3000 chars → mock POST returning 502 → call `client.get()` → verify `TransientError` for non-snapshot entities

## Acceptance Criteria (Gherkin absoluto)

### AC-1: Batch POST non-200 raises typed error through client.get()

```
Given a query whose serialized URL exceeds 3000 characters
  And the batch POST endpoint returns HTTP 400 with {"error": {"message": "bad filter"}}
When client.get("WorkItems", **params) is called with query params that exceed the URL limit
Then a BadRequestError is raised with message containing "bad filter"
```

### AC-2: aiohttp.ClientError in batch POST raises TransientError with chained cause

```
Given a query whose serialized URL exceeds 3000 characters
  And self._session.post() raises aiohttp.ClientError("connection reset")
When client.get("WorkItems", **params) is called
Then a TransientError is raised with message containing "connection reset"
  And exc.__cause__ is an aiohttp.ClientError
```

### AC-3: Non-snapshot entity batch POST passes error through client.get()

```
Given a query whose serialized URL exceeds 3000 characters
  And the batch POST endpoint returns HTTP 502
When client.get("WorkItems", **params) is called
Then a TransientError is raised
```

Note: AC-3 replaces the original AC-3/AC-4 (already covered by existing test_batch.py unit tests) and AC-5 (moved to DoD as coverage constraint).

## NFRs

- **No mocking framework changes:** Use existing aioresponses pattern for HTTP responses
- **ClientError simulation:** `aioresponses` cannot raise `aiohttp.ClientError`. Tests for AC-2 MUST use `unittest.mock.patch.object(client._session, "post")` or similar to inject the exception at the session level
- **Retry awareness:** AC-2 must account for `@with_retry` (3 attempts before TransientError propagates). Mock must raise ClientError on ALL retries
- **Isolation:** Tests must not make real HTTP requests
- **Determinism:** All tests must be repeatable without network

## INVEST self-score

- **I**ndependent: 8/10 — test-only change; mocking ClientError requires patching client session
- **N**egotiable: 8/10 — exact test structure negotiable; AC-2 mocking approach is explicit
- **V**aluable: 9/10 — covers genuine gaps: batch POST path and ClientError handler
- **E**stimable: 8/10 — ~60 LOC of tests; ClientError mocking via patch adds slight complexity
- **S**mall: 9/10 — one new test file
- **T**estable: 8/10 — pure mocked tests; AC-2 depends on correct patch setup

Média: 8.3/10

## Out of scope

- Integration tests with real HTTP
- Changes to production code (src/)
- Adding new test infrastructure
- End-to-end batch flow testing
- Re-testing the URL-length-switching logic (already covered by test_batch.py unit tests)
- Re-testing parse_response() directly for individual status codes (already covered by test_http_coverage.py)

## Test plan

- AC-1 → test_batch_post_non_200 → build URL > 3000 chars via query params → mock aioresponses POST returning 400 → call client.get() → verify BadRequestError with message
- AC-2 → test_client_error_raises_transient_error → build URL > 3000 chars → patch client._session.post to raise ClientError → call client.get() → verify TransientError + chained __cause__
- AC-3 → test_batch_post_non_snapshot_502 → build URL > 3000 chars → mock aioresponses POST returning 502 → call client.get() → verify TransientError

## DoD

- [ ] AC-1 to AC-3 pass
- [ ] `uv run pytest --cov=ado_odata_async --cov-fail-under=85` GREEN
- [ ] `uv run pytest -q` exit 0
- [ ] `uv run ruff check .` exit 0
- [ ] `uv run mypy src/` exit 0
- [ ] `bash scripts/audit.sh` exit 0
