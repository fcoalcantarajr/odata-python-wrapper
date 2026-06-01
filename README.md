# ado-odata-async

A Python async client for Azure DevOps Analytics OData. It queries work items, history, and flow metrics from Azure Boards using the OData API — no REST boilerplate, no `requests`, no dict gymnastics.

---

## What is this?

This library lets you pull data from Azure Boards (work items, revision history, flow metrics) using the Analytics OData API. If you need cycle time, throughput, or WIP from Azure DevOps, this wraps the query layer so you write Python instead of raw OData URLs.

---

## Start here

New to this library? Follow this path:

1. **[`docs/getting-started.md`](docs/getting-started.md)** — install, create a PAT, configure `.env`, run your first query (5 min).
2. **[`docs/concepts.md`](docs/concepts.md)** — what OData is, WorkItems vs Revisions vs Snapshot, flow metrics, async/await basics.
3. **[`docs/cookbook.md`](docs/cookbook.md)** — 8 practical recipes: filter, paginate, cycle time, CSV export, error handling.
4. **[`docs/glossary.md`](docs/glossary.md)** — alphabetical reference of every technical term used here.
5. **[`docs/troubleshooting.md`](docs/troubleshooting.md)** — symptom → cause → solution for common errors (401, 400, 203, etc.).

---

## Docs index

| Doc | What's inside | Open this when… |
|---|---|---|
| [getting-started.md](docs/getting-started.md) | Step-by-step install, PAT creation, `.env` setup, first working script. | You're starting from zero. |
| [concepts.md](docs/concepts.md) | OData explained, WorkItems vs Revisions vs Snapshot, flow metrics, async/await basics. | You want to understand what the library is doing under the hood. |
| [cookbook.md](docs/cookbook.md) | 8 recipes: filter, paginate, cycle time, throughput, WIP, CSV export, error handling. | You know the basics and want to do something specific. |
| [glossary.md](docs/glossary.md) | Alphabetical list of every term (OData, PAT, WIP, cycle time, etc.). | You hit a term you don't recognize. |
| [troubleshooting.md](docs/troubleshooting.md) | Symptom → cause → solution for 401, 400, 203, module errors, long URLs. | Something isn't working and you need a quick fix. |
| [intern_first_query.py](examples/intern_first_query.py) | Minimal script: count work items grouped by StateCategory. | You want the smallest runnable example. |
| [demo_flow_metrics.py](demo_flow_metrics.py) | Full demo: cycle time, weekly throughput, daily WIP (109 lines). | You want to see a real-world flow metrics calculation. |

---

## Quickstart

> ⏱ **5 minutes** from clone to first result.

```python
"""First query with ado-odata-async."""
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env from current directory (not script directory)
env_path = Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Read credentials — supports ADO_* and AZURE_DEVOPS_* as fallback
pat = os.environ.get("ADO_PAT") or os.environ.get("AZURE_DEVOPS_PAT") or ""
org = os.environ.get("ADO_ORG") or os.environ.get("AZURE_DEVOPS_ORG") or ""
project = os.environ.get("ADO_PROJECT") or os.environ.get("AZURE_DEVOPS_PROJECT") or ""

if not pat or not org or not project:
    print("ERROR: set ADO_PAT, ADO_ORG and ADO_PROJECT in .env")
    sys.exit(1)

print(f"Connecting to {org}/{project} ...")


async def main() -> None:
    from ado_odata_async import AdoODataClient
    from ado_odata_async.query import Filter

    async with AdoODataClient(org=org, project=project, pat=pat) as client:
        result = await (
            client.query("WorkItems")
            .select("WorkItemId", "Title", "State", "WorkItemType")
            .top(5)
            .get()
        )

    items = result.get("value", [])
    print(f"\nFound {len(items)} work items:\n")
    for item in items:
        print(f"  #{item['WorkItemId']}  [{item['WorkItemType']}]  {item['State']:20s}  {item['Title']}")


asyncio.run(main())
```

> **Before running**: create a `.env` file in the project root with:
> ```
> ADO_ORG=your-org
> ADO_PROJECT=your-project
> ADO_PAT=your-personal-access-token
> ```
> See the [getting started guide](docs/getting-started.md) for step-by-step instructions.

---

## PAT security

> ⚠️ Your PAT (Personal Access Token) is a password that grants read access to your Azure DevOps organization. Treat it like your bank password.

1. **Minimum scope**: when creating the PAT, select only:
   - `Work Items (Read)`
   - `Analytics (Read)`
   - Nothing else. Least privilege.

2. **Short expiration**: set expiration to **30 days** (max 90). Set a calendar reminder to renew before it expires.

3. **Never commit**: the PAT must never be version-controlled. The `.env` file is already in `.gitignore` — confirm before `git add`.

4. **Periodic rotation**: at each new project or end of internship, revoke the old token and generate a new one. Follow your institution's security policy.

5. **Zero sharing**: don't share your PAT via email, chat, or code. If someone needs access, have them generate their own token.

---

## License

MIT © OhMyOpenCode
