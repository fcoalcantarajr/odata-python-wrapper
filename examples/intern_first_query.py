"""Intern's first query: count work items grouped by StateCategory."""

import asyncio
import os
from pathlib import Path

# Load .env from root
env_path = Path(".env")
if env_path.exists():
    try:
        from dotenv import load_dotenv

        load_dotenv(dotenv_path=env_path)
    except ImportError:
        # dotenv not available; parse .env manually
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

org = os.environ.get("AZURE_DEVOPS_ORG") or ""
project = os.environ.get("AZURE_DEVOPS_PROJECT") or ""
pat = os.environ.get("AZURE_DEVOPS_PAT") or ""

if not pat or not org or not project:
    print("ERROR: missing AZURE_DEVOPS_ORG / AZURE_DEVOPS_PROJECT / AZURE_DEVOPS_PAT in .env")
    exit(1)


async def main() -> None:
    """Fetch count of work items grouped by StateCategory."""
    from ado_odata_async import AdoODataClient
    from ado_odata_async.query import Apply

    async with AdoODataClient(org=org, project=project, pat=pat) as client:
        result = await (
            client.query("WorkItems")
            .apply(Apply().groupby("StateCategory").aggregate("$count", alias="Count"))
            .get()
        )

    rows = result.get("value", [])
    if not rows:
        print("No data returned")
        exit(1)

    print(f"\nWork items count by StateCategory ({len(rows)} categories):\n")
    for row in rows:
        category = row.get("StateCategory") or "(none)"
        count = row.get("Count") or 0
        print(f"  {category!s:20s}  {count}")

    print(f"\nTotal rows: {len(rows)}")


asyncio.run(main())
