"""intern_first_query.py — primeira métrica real do projeto.

Fetches: total count of work items, grouped by StateCategory
(Proposed / InProgress / Completed / Removed — universal across languages).

Uses the OData $apply aggregation DSL (groupby + $count) so the server returns
a single, small, pre-aggregated result — no client-side iteration over rows.

Reference: docs/cookbook.md (Receita 8 — Apply DSL com aggregate).
"""

import asyncio
import os
import sys
from pathlib import Path

env_path = Path(".env")
if env_path.exists():
    try:
        from dotenv import load_dotenv  # type: ignore[import-not-found]

        load_dotenv(dotenv_path=env_path)
    except ModuleNotFoundError:
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
    print("ERRO: defina AZURE_DEVOPS_PAT, AZURE_DEVOPS_ORG e AZURE_DEVOPS_PROJECT no .env")
    sys.exit(1)

print(f"Conectando em {org}/{project} ...")
print("Buscando: contagem de work items agrupada por StateCategory ...\n")


async def main() -> None:
    from ado_odata_async import AdoODataClient
    from ado_odata_async.query import Apply

    async with AdoODataClient(org=org, project=project, pat=pat) as client:
        result = await (
            client.query("WorkItems")
            .apply(Apply().groupby("StateCategory").aggregate("$count", alias="Count"))
            .top(50)
            .get()
        )

    rows = result.get("value", [])
    if not rows:
        print("Nenhum resultado retornado pelo servidor.")
        return

    ordem_conhecida = ["Proposed", "InProgress", "Completed", "Removed", "Resolved"]
    rows_sorted = sorted(
        rows,
        key=lambda r: (
            ordem_conhecida.index(r["StateCategory"])
            if r.get("StateCategory") in ordem_conhecida
            else 99
        ),
    )

    total = sum(int(r.get("Count", 0)) for r in rows_sorted)

    print("Distribuição de work items por StateCategory")
    print(f"(total: {total} work items)\n")
    print(f"  {'Categoria':<15s}  {'Qtd':>7s}  {'%':>6s}  Distribuição")
    print(f"  {'-'*15}  {'-'*7}  {'-'*6}  {'-'*40}")

    for r in rows_sorted:
        cat = r.get("StateCategory") or "(unclassified)"
        qty = int(r.get("Count", 0))
        pct = (qty / total * 100) if total else 0
        barra = "█" * min(int(pct / 2), 50)
        print(f"  {cat:<15s}  {qty:>7d}  {pct:>5.1f}%  {barra}")


asyncio.run(main())
