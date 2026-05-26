#!/usr/bin/env -S uv run python
"""Real-data flow metrics from ADO Analytics OData."""

import asyncio, json, os, re, sys
from collections import Counter
from datetime import UTC, datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
pat = os.environ.get("AZURE_DEVOPS_PAT") or os.environ.get("ADO_PAT") or ""
org = os.environ.get("AZURE_DEVOPS_ORG") or ""
project = os.environ.get("AZURE_DEVOPS_PROJECT") or ""

if not pat or not org or not project:
    # Broader env var search per spec regex
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
        query = {"$filter": "StateCategory eq 'Completed'",
                 "$select": "WorkItemId,Title,State,WorkItemType,CreatedDate,ActivatedDate,"
                            "ClosedDate,StateChangeDate",
                 "$orderby": "ClosedDate desc"}
        async for page in client.paginate("WorkItems", top=200, query=query):
            items.extend(page.get("value", []))
            print(f"  page: {len(page.get('value',[]))} items (total {len(items)})")
            if len(items) >= 500:
                break

        if len(items) < 10:
            print(f"FATAL: only {len(items)} items", file=sys.stderr); sys.exit(1)

        os.makedirs("out", exist_ok=True)
        with open("out/raw_sample.json", "w") as f:
            json.dump(items[:10], f, indent=2, default=str)

        def _parse_dt(v):
            if not v: return None
            try: return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except: return None

        cycle_deltas = []
        for i in items:
            ad, cd = _parse_dt(i.get("ActivatedDate")), _parse_dt(i.get("ClosedDate"))
            if ad and cd:
                d = (cd - ad).total_seconds() / 86400
                if d >= 0: cycle_deltas.append(round(d, 2))
        cycle_deltas.sort()
        cc = len(cycle_deltas)
        def pct(p): return cycle_deltas[max(0, int(cc * p / 100) - 1)] if cc else 0
        cycle_time = {"count": cc, "median_days": cycle_deltas[cc // 2] if cc else 0,
                      "p50": pct(50), "p85": pct(85), "p95": pct(95), "values_days": cycle_deltas}

        throughput = Counter()
        for i in items:
            cd = _parse_dt(i.get("ClosedDate"))
            if cd:
                y, w, _ = cd.isocalendar(); throughput[f"{y}-W{w:02d}"] += 1
        l12w_set = {(datetime.now(UTC) - timedelta(weeks=i)).isocalendar() for i in range(12)}
        l12w_keys = {f"{y}-W{w:02d}" for y, w, _ in l12w_set}
        throughput_weekly = dict(sorted((k, v) for k, v in throughput.items() if k in l12w_keys))

        wip = {}
        now = datetime.now(UTC)
        for i in range(30):
            d = now - timedelta(days=i); ds = d.strftime("%Y-%m-%d")
            wip[ds] = sum(1 for item in items if
                          (c := _parse_dt(item.get("CreatedDate"))) and c.date() <= d.date() and
                          (not (cl := _parse_dt(item.get("ClosedDate"))) or cl.date() >= d.date()))
        wip_daily = dict(sorted(wip.items()))

        metrics = {"meta": {"project": project, "pulled_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "sample_size": len(items), "library_version": lib_version},
                   "cycle_time": cycle_time, "throughput_weekly": throughput_weekly, "wip_daily": wip_daily}
        with open("out/metrics.json", "w") as f:
            json.dump(metrics, f, indent=2, default=str)

        print(f"\n{'='*60}\nFLOW METRICS SUMMARY\n{'='*60}")
        print(f"Total items pulled:       {len(items)}")
        print(f"Items with cycle time:    {cc}")
        print(f"Cycle time p50/p85/p95:   {cycle_time['p50']:.1f} / {cycle_time['p85']:.1f} / {cycle_time['p95']:.1f} days")
        if throughput_weekly:
            print(f"Throughput weeks:         {min(throughput_weekly)} to {max(throughput_weekly)}")
            print(f"Total closed (12w):       {sum(throughput_weekly.values())}")
        if wip_daily:
            wv = list(wip_daily.values())
            print(f"WIP range (30d):          {min(wv)} - {max(wv)} active items")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())


