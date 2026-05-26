#!/usr/bin/env -S uv run python
"""Real-data flow metrics from ADO Analytics OData."""
import asyncio, json, os, re, sys
from collections import Counter
from datetime import UTC, datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
pat = os.environ.get("AZURE_DEVOPS_PAT") or ""
org = os.environ.get("AZURE_DEVOPS_ORG") or ""
project = os.environ.get("AZURE_DEVOPS_PROJECT") or ""
if not pat or not org or not project:
    for k, v in os.environ.items():
        if re.match(r"^(ADO|AZURE)_(DEVOPS_)?(PAT|ORG|ORGANIZATION|PROJECT)=", k + "="):
            if "PAT" in k: pat = pat or v
            if "ORG" in k: org = org or v
            if "PROJECT" in k: project = project or v
    if not pat or not org or not project:
        print("FATAL: missing ADO env vars", file=sys.stderr); sys.exit(1)
print(f"org={org}  project={project}  pat=PAT(****{pat[-4:]})")


async def main() -> None:
    from ado_odata_async import AdoODataClient, __version__ as lib_version

    async with AdoODataClient(org=org, project=project, pat=pat) as client:
        items: list[dict] = []

        # Query 1: closed items (drives cycle_time + throughput)
        async for page in client.paginate("WorkItems", top=200, query={
            "$filter": "StateCategory eq 'Completed'",
            "$select": "WorkItemId,Title,State,WorkItemType,CreatedDate,ActivatedDate,ClosedDate,StateChangeDate",
            "$orderby": "ClosedDate desc",
        }):
            items.extend(page.get("value", []))
            if len(items) >= 500: break

        # Query 2: open / in-progress items (for real WIP — StateCategory not Completed)
        async for page in client.paginate("WorkItems", top=200, query={
            "$filter": "StateCategory ne 'Completed'",
            "$select": "WorkItemId,Title,State,WorkItemType,CreatedDate,ActivatedDate,ClosedDate,StateChangeDate",
            "$orderby": "CreatedDate desc",
        }):
            items.extend(page.get("value", []))
            if len(items) >= 1000: break

        if len(items) < 10:
            print(f"FATAL: only {len(items)} items", file=sys.stderr); sys.exit(1)

    os.makedirs("out", exist_ok=True)
    with open("out/raw_sample.json", "w") as f:
        json.dump(items[:10], f, indent=2, default=str)

    def parse_dt(v):
        if not v: return None
        try: return datetime.fromisoformat(v.replace("Z", "+00:00"))
        except: return None

    # Cycle time: ActivatedDate→ClosedDate (first active→closed). Drop zero-day items (NOT zeros per DoD).
    vals = sorted([
        round((cd - ad).total_seconds() / 86400, 2)
        for i in items
        if (ad := parse_dt(i.get("ActivatedDate"))) and (cd := parse_dt(i.get("ClosedDate"))) and cd > ad
        and round((cd - ad).total_seconds() / 86400, 2) > 0
    ])
    cc = len(vals)
    def pct(p): return vals[min(cc - 1, int(cc * p / 100))] if cc else 0.0
    cycle_time = dict(count=cc, median_days=pct(50), p50=pct(50), p85=pct(85), p95=pct(95), values_days=vals)

    # Throughput: ClosedDate per ISO week, last 12 weeks
    tw = Counter()
    for i in items:
        if cd := parse_dt(i.get("ClosedDate")):
            y, w, _ = cd.isocalendar(); tw[f"{y}-W{w:02d}"] += 1
    l12 = sorted({(datetime.now(UTC) - timedelta(weeks=i)).strftime("%G-W%V") for i in range(12)})
    throughput_weekly = {k: tw.get(k, 0) for k in l12}

    # WIP: items active per day, last 30 days
    now, wip = datetime.now(UTC), {}
    for i in range(30):
        d = (now - timedelta(days=i)).date(); ds = d.isoformat()
        wip[ds] = sum(
            1 for item in items
            if (c := parse_dt(item.get("CreatedDate"))) and c.date() <= d
            and (not (cl := parse_dt(item.get("ClosedDate"))) or cl.date() >= d)
        )
    wip_daily = dict(sorted(wip.items()))

    metrics = dict(
        meta=dict(project=project, pulled_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                  sample_size=len(items), library_version=lib_version),
        cycle_time=cycle_time, throughput_weekly=throughput_weekly, wip_daily=wip_daily,
    )
    with open("out/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2, default=str)

    print(f"\n{'='*60}\nFLOW METRICS SUMMARY\n{'='*60}")
    print(f"Total items pulled:       {len(items)}")
    print(f"Items with cycle time:    {cc}")
    print(f"Cycle time p50/p85/p95:   {pct(50):.1f} / {pct(85):.1f} / {pct(95):.1f} days")
    print(f"Throughput weeks:         {l12[0]} to {l12[-1]}")
    print(f"Total closed (12w):       {sum(throughput_weekly.values())}")
    wv = list(wip_daily.values())
    print(f"WIP range (30d):          {min(wv)} - {max(wv)} active items")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
