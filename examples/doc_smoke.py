"""Doc-driven smoke test — junior-user seat.

This script is written from README.md + docs/ ONLY.
No src/ was opened during writing. If it fails, the DOCS are wrong.

Loads credentials from .env exactly as the docs instruct.
Pulls real Azure DevOps Analytics metrics the docs advertise.
Prints a compact, human-readable report.
"""

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

# Credential vars — docs say: AZURE_DEVOPS_ORG, AZURE_DEVOPS_PROJECT, AZURE_DEVOPS_PAT
ORG = os.environ.get("AZURE_DEVOPS_ORG", "")
PROJECT = os.environ.get("AZURE_DEVOPS_PROJECT", "")
PAT = os.environ.get("AZURE_DEVOPS_PAT", "")


async def main() -> None:
    # --- Imports from README.md ---
    from ado_odata_async import (
        AdoODataClient,
        compute_baseline_metrics,
        compute_flow_times,
        compute_plan_history,
    )
    from ado_odata_async.query import Apply, Filter

    print("=" * 60)
    print("DOC-DRIVEN SMOKE TEST — junior-user seat")
    print("=" * 60)
    print(f"Org:      {ORG}")
    print(f"Project:  {PROJECT}")
    print(f"PAT:      {PAT[:6]}...")
    print()

    # --- 1. Basic query (README Quickstart) ---
    print("--- 1. Basic Query (README Quickstart) ---")
    async with AdoODataClient(org=ORG, project=PROJECT, pat=PAT) as client:
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
        print(f"  {row['State']:20s}  {row['Count']}")
    print()

    # --- 2. Plan History (README Flow Metrics section) ---
    print("--- 2. Plan History (compute_plan_history) ---")
    async with AdoODataClient(org=ORG, project=PROJECT, pat=PAT) as client:
        wi_result = await (
            client.query("WorkItems")
            .select("WorkItemId", "CreatedDate", "StateCategory", "TargetDate", "CompletedDate")
            .top(200)
            .get()
        )
    items = wi_result.get("value", [])
    plan = compute_plan_history(items)
    print(f"  created_date:   {plan.created_date}")
    print(f"  oldest_card:    {plan.oldest_card_date}")
    print(f"  on_time_rate:   {plan.on_time_rate:.1%}")
    print()

    # --- 3. Flow Times (README Flow Metrics section) ---
    print("--- 3. Flow Times (compute_flow_times) ---")
    # Fetch revisions for first work item
    if items:
        first_id = items[0].get("WorkItemId")
        if first_id:
            async with AdoODataClient(org=ORG, project=PROJECT, pat=PAT) as client:
                rev_result = await (
                    client.query("WorkItemRevisions")
                    .filter(Filter.eq("WorkItemId", first_id))
                    .select("WorkItemId", "State", "ChangedDate")
                    .top(50)
                    .get()
                )
            revisions = rev_result.get("value", [])
            flow = compute_flow_times(revisions)
            print(f"  WorkItemId:          {first_id}")
            print(f"  state_history:       {len(flow.state_history)} transitions")
            print(f"  time_in_queue_days:  {flow.time_in_queue_days}")
            print(f"  time_in_progress:    {flow.time_in_progress_days} days")
    print()

    # --- 4. Baseline Metrics (README Flow Metrics section) ---
    print("--- 4. Baseline Metrics (compute_baseline_metrics) ---")
    if items:
        first_id = items[0].get("WorkItemId")
        if first_id:
            async with AdoODataClient(org=ORG, project=PROJECT, pat=PAT) as client:
                rev_result = await (
                    client.query("WorkItemRevisions")
                    .filter(Filter.eq("WorkItemId", first_id))
                    .select("WorkItemId", "TargetDate", "ChangedDate")
                    .top(50)
                    .get()
                )
            revisions = rev_result.get("value", [])
            baseline = compute_baseline_metrics(revisions)
            print(f"  WorkItemId:            {first_id}")
            print(f"  original_target_date:  {baseline.original_target_date}")
            print(f"  target_date_changes:   {baseline.target_date_changes}")
            print(f"  replanned:             {baseline.replanned}")
    print()

    print("=" * 60)
    print("SMOKE TEST COMPLETE — all sections passed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
