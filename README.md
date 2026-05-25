# ado-odata-async

Async Python client for **Azure DevOps Analytics OData** focused on **Work Tracking** (Boards).

- OData **v4.0-preview** (ADR-001)
- `aiohttp` + `pydantic` + `tenacity`
- Immutable chainable [QueryBuilder](https://github.com/ohmyopencode/odata-python-wrapper/blob/main/src/ado_odata_async/query/_builder.py)
- SDLC **SDD + TDD** with autonomous agents (opencode + omo)

## Installation

```bash
uv add ado-odata-async
```

Requires Python ≥ 3.12.

## Quick start

```python
import asyncio
from ado_odata_async import AdoODataClient
from ado_odata_async.query import Filter

async def main() -> None:
    async with AdoODataClient(
        org="myorg",
        project="myproject",
        pat="your-pat-token",
    ) as client:
        # Simple query
        result = await (
            client.query("WorkItems")
            .filter(Filter.eq("State", "Active"))
            .select("WorkItemId", "Title", "State")
            .top(10)
            .get()
        )
        for item in result["value"]:
            print(item["WorkItemId"], item["Title"])

asyncio.run(main())
```

## Features

| Feature | Description |
|---------|-------------|
| **Chainable QueryBuilder** | Immutable `.filter()`, `.select()`, `.top()`, `.skip()`, `.orderby()`, `.expand()`, `.apply()` |
| **Filter DSL** | Expression tree with `Filter.eq/ne/and_/or_/not_/contains` — auto-escaping and parentheses |
| **Apply DSL** | `$apply` builder for `WorkItemSnapshot` with `groupby` + `aggregate` |
| **Pagination** | Async iterator via `$skip`/`$top` or `@odata.nextLink` |
| **Batch** | Automatic `POST $batch` when URL exceeds 3000 chars |
| **Retry** | Exponential backoff with jitter, retries only `TransientError`/`RateLimitError` |
| **Typed errors** | `AuthenticationError`, `BadRequestError`, `RateLimitError`, `TransientError` |
| **Entities** | Pydantic frozen+strict models: `WorkItem`, `WorkItemRevisions`, `Iteration`, `Project`, `Team`, `Area`, `Date`, `User`, `WorkItemType`, `WorkItemLink`, `WorkItemBoardSnapshot` |
| **Immutability** | All builders return new instances — no mutation |

## Usage examples

### Filter with pagination

```python
from ado_odata_async.query import Filter

async for page in (
    client.query("WorkItems")
    .filter(Filter.and_(Filter.eq("WorkItemType", "Bug"), Filter.eq("State", "Active")))
    .select("WorkItemId", "Title")
    .paginate(top=50)
):
    for item in page["value"]:
        print(item["WorkItemId"], item["Title"])
```

### Apply + groupby for WorkItemSnapshot

WorkItemSnapshot requires `$apply` with `groupby` on `DateSK` (HR-13 gotcha 4):

```python
from ado_odata_async.query import Apply

result = await (
    client.query("WorkItemSnapshot")
    .apply(
        Apply()
        .filter(Filter.eq("State", "Active"))
        .groupby("DateSK", "State")
        .aggregate("Count", "WorkItemId")
    )
    .top(10)
    .get()
)
```

### Fetch single WorkItem

```python
wi = await client.get_workitem(42)
print(f"#{wi.WorkItemId}: {wi.Title} ({wi.WorkItemType})")
```

### Error handling

```python
from ado_odata_async import AuthenticationError, BadRequestError

try:
    result = await client.get("WorkItems", **{"$filter": "WorkItemType eq 'Bug'"})
except AuthenticationError:
    print("PAT inválido ou expirado")
except BadRequestError as e:
    print(f"Bad request: {e}")
```

See [`docs/cookbook.md`](docs/cookbook.md) for 12 worked examples.

## Architecture

```
Layer           Module                  Responsibility
──────────────────────────────────────────────────────
Auth            auth.py                 PAT → BasicAuth, mask helper
HTTP            _http.py                Response parsing, error mapping
Client          client.py               Single ClientSession, top-level API
Retry           retry.py                Tenacity expo+jitter, TransientError only
Query           query/_filter.py        Filter expression tree
                query/_apply.py         Apply DSL (groupby + aggregate)
                query/_serialize.py     Canonical query serialization (HR-9)
                query/_batch.py         URL > 3000 → POST $batch
                query/_builder.py       Fluent QueryBuilder
Pagination      pagination.py           Async iterator over $skip/nextLink
Entities        entities/               Pydantic frozen+strict models
Exceptions      exceptions.py           Typed exception hierarchy
```

Detailed architecture: [`docs/architecture.md`](docs/architecture.md).

## Project conventions

- **HARD RULES**: See [`AGENTS.md`](AGENTS.md) — 22 hard rules covering auth, retry, query serialization, type safety, and more.
- **SDLC**: Every feature starts with a spec (`specs/NNN-slug.md`) approved by `/spec-check`, then test-first (RED), then implementation (GREEN).
- **8 gotchas**: Azure DevOps Analytics OData has 8 critical gotchas documented in [`AGENTS.md`](AGENTS.md) — PAT auth, query option order, URL length, snapshot requirements, etc.

## Development

```bash
# Setup
uv sync

# Test
uv run pytest

# Static analysis
uv run ruff check .
uv run mypy src/

# Audit
bash scripts/audit.sh

# Coverage
uv run pytest --cov=ado_odata_async --cov-fail-under=85
```

## ADRs

Architecture Decision Records in [`docs/decisions.md`](docs/decisions.md):

| ADR | Decision |
|-----|----------|
| 001 | OData v4.0-preview default |
| 002 | Auth error mapping (203+text/html → AuthenticationError) |
| 003 | Retry strategy (tenacity expo+jitter, TransientError only) |
| 004 | Pagination async iterator ($skip/$top + nextLink) |
| 005 | Filter DSL (expression tree with escape) |
| 006 | Pydantic frozen + strict + extra-forbid |
| 007 | Query serialization order (HR-9) |
| 008 | Batch POST for URLs > 3000 chars |
| 009 | Notion MCP as canonical spec/ADR store |
| 010 | Scaffolding via opencode |
| 011 | Fluent API QueryBuilder |