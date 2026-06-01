# ado-odata-async

Async Python client for Azure DevOps Analytics OData.

[![License: MPL 2.0](https://img.shields.io/badge/license-MPL%202.0-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](pyproject.toml)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Quickstart](#quickstart)
- [Example output](#example-output)
- [Usage](#usage)
- [Docs index](#docs-index)
- [Troubleshooting](#troubleshooting)
- [License](#license)
- [Contributing](#contributing)
- [Acknowledgments](#acknowledgments)

---

## Overview

This library wraps the Azure DevOps Analytics OData API — eliminates raw URL construction, handles auth, pagination, retry, and the `$apply` DSL. For developers who need cycle time, throughput, or WIP from Azure Boards without writing raw OData URLs.

---

## Features

- **Async-first** — built on `aiohttp`, no blocking calls
- **`$apply` DSL** — chain `filter()`, `groupby()`, `aggregate()` without raw OData strings
- **Pagination** — automatic `@odata.nextLink` handling via `paginate()`
- **Retry with backoff** — `tenacity`-based retries on transient failures
- **Pydantic validation** — strict, frozen models for all responses
- **Zero external auth deps** — uses `aiohttp.BasicAuth` directly with your PAT

---

## Requirements

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** package manager — install with `pip install uv` or visit the link
- **Azure DevOps Personal Access Token** with these scopes:
  - `Work Items (Read)`
  - `Analytics (Read)`
- **Org name** (e.g. `myorg`) and **project name** (e.g. `myproject`) from your Azure DevOps URL

---

## Installation

**From git:**

```bash
uv add git+https://github.com/fcoalcantarajr/odata-python-wrapper@main
```

**Local dev:**

```bash
git clone https://github.com/fcoalcantarajr/odata-python-wrapper.git
cd odata-python-wrapper
uv sync
```

---

## Configuration

Create a `.env` file in your project root with these three variables:

```
AZURE_DEVOPS_ORG=your-org-name
AZURE_DEVOPS_PROJECT=your-project-name
AZURE_DEVOPS_PAT=your-personal-access-token
```

Replace `your-org-name`, `your-project-name`, and `your-personal-access-token` with your actual Azure DevOps values.

**PAT security:** Use minimum scopes (Work Items Read + Analytics Read only), set a short expiration (30 days), and never commit `.env` to version control.

---

## Quickstart

```python
"""First query with ado-odata-async."""
import asyncio
import os
from pathlib import Path


def _load_dotenv() -> None:
    """Load .env file into os.environ (no external deps)."""
    env_path = Path(".env")
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()

async def main() -> None:
    from ado_odata_async import AdoODataClient
    from ado_odata_async.query import Apply, Filter

    async with AdoODataClient(
        org=os.environ["AZURE_DEVOPS_ORG"],
        project=os.environ["AZURE_DEVOPS_PROJECT"],
        pat=os.environ["AZURE_DEVOPS_PAT"],
    ) as client:
        result = await (
            client.query("WorkItems")
            .apply(
                Apply()
                .filter(Filter.eq("StateCategory", "Completed"))
                .groupby("State")
                .aggregate("$count", alias="Count")
            )
            .get()
        )

    for row in result.get("value", []):
        print(f"{row['State']:20s}  {row['Count']}")

asyncio.run(main())
```

Save the script as `quickstart.py` and run it:

```bash
uv run python quickstart.py
```

---

## Example output

The quickstart filters for `StateCategory eq 'Completed'` and groups by `State`. In Azure DevOps, the Completed category includes states like Closed, Done, and Removed:

```
Closed               158
Done                 42
Removed               3
```

---

## Usage

**Simple select with top:**

```python
result = await (
    client.query("WorkItems")
    .select("WorkItemId", "Title", "State")
    .top(5)
    .get()
)
```

**Pagination for large datasets:**

Use the `paginate()` method to automatically handle `@odata.nextLink` continuation tokens:

```python
async for page in client.query("WorkItems").select("WorkItemId", "Title").paginate():
    for item in page.get("value", []):
        print(item["WorkItemId"], item["Title"])
```

---

## Docs index

| Doc | What's inside | Open this when… |
|---|---|---|
| [getting-started.md](docs/getting-started.md) | Step-by-step install, PAT creation, .env setup | You're starting from zero |
| [concepts.md](docs/concepts.md) | OData explained, WorkItems vs Revisions vs Snapshot | You want to understand the library |
| [cookbook.md](docs/cookbook.md) | 8 recipes: filter, paginate, cycle time, CSV export | You know the basics |
| [glossary.md](docs/glossary.md) | Alphabetical term reference | You hit a term you don't know |
| [troubleshooting.md](docs/troubleshooting.md) | Symptom → cause → solution for errors | Something isn't working |
| [architecture.md](docs/architecture.md) | Internal layers: Auth → HTTP → Client → Query → Serializer | You want to understand how the code is organized |
| [decisions.md](docs/decisions.md) | Architecture Decision Records (ADRs) | You want to know why certain design choices were made |
| [intern_first_query.py](examples/intern_first_query.py) | Minimal runnable example (uses `python-dotenv` if available) | You want the smallest script |

---

## Troubleshooting

See [troubleshooting.md](docs/troubleshooting.md) for full symptom → cause → solution tables.

**Top 2 gotchas:**

1. **HTTP 203 = PAT invalid.** ADO returns 203 with `text/html` when the PAT is expired or malformed. This is not retryable — regenerate the token.

2. **Flat vs nested `$apply`.** The library handles `$apply` clause ordering automatically, but your `filter()` must come before `groupby()` — filters inside `$apply` scope rows before aggregation.

---

## License

Licensed under the Mozilla Public License 2.0. See [LICENSE](LICENSE) for details. You can use this as a dependency in any project; changes to this library's own files must stay MPL-2.0.

---

## Contributing

Contributions welcome! Open an issue or submit a pull request. Run `uv run pytest` and `uv run ruff check .` before submitting.

---

## Acknowledgments

Built with [OhMyOpenCode](https://ohmyopencode.com)
