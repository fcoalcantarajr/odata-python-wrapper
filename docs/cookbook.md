**English** | [Português](#português-brasil)

# Cookbook: 8 practical recipes

> All recipes below use tested code and work with real Azure DevOps data.
> They assume credentials are in `.env` as described in the [getting started guide](getting-started.md).

---

## 1. List the 10 most recently created work items

**When you need this**: take a first look at what's happening in the project — see the most recent items.

```python
"""Recipe 1: list most recent work items."""
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
org = os.environ.get("AZURE_DEVOPS_ORG") or ""
project = os.environ.get("AZURE_DEVOPS_PROJECT") or ""
pat = os.environ.get("AZURE_DEVOPS_PAT") or ""


async def main() -> None:
    from ado_odata_async import AdoODataClient
    from ado_odata_async.query import Filter

    async with AdoODataClient(org=org, project=project, pat=pat) as client:
        result = await (
            client.query("WorkItems")
            .select("WorkItemId", "Title", "WorkItemType", "State", "CreatedDate")
            .orderby("CreatedDate desc")
            .top(10)
            .get()
        )

    for item in result.get("value", []):
        print(f"#{item['WorkItemId']:6d}  [{item['WorkItemType']:10s}]  "
              f"{item['State']:15s}  {item['CreatedDate'][:10]}  {item['Title']}")


asyncio.run(main())
```

**Expected output**:
```
#   42  [Task      ]  Done             2025-05-20  Create login screen
#   43  [Bug       ]  Done             2025-05-19  Fix timeout
#  ...
```

**How it works**: `orderby("CreatedDate desc")` sorts from newest to oldest. `top(10)` limits to 10 results. `select` reduces the amount of data transferred.

---

## 2. Filter by state and date range

**When you need this**: find open bugs from the last two weeks.

```python
"""Recipe 2: filter active bugs from the last 2 weeks."""
import asyncio
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
org = os.environ.get("AZURE_DEVOPS_ORG") or ""
project = os.environ.get("AZURE_DEVOPS_PROJECT") or ""
pat = os.environ.get("AZURE_DEVOPS_PAT") or ""

days_ago = (datetime.now(UTC) - timedelta(days=14)).isoformat()


async def main() -> None:
    from ado_odata_async import AdoODataClient
    from ado_odata_async.query import Filter

    filtro = Filter.and_(
        Filter.eq("WorkItemType", "Bug"),
        Filter.eq("StateCategory", "InProgress"),
        Filter.ge("CreatedDate", days_ago),
    )

    async with AdoODataClient(org=org, project=project, pat=pat) as client:
        result = await (
            client.query("WorkItems")
            .filter(filtro)
            .select("WorkItemId", "Title", "CreatedDate")
            .top(20)
            .get()
        )

    print(f"Open bugs in the last 2 weeks: {len(result.get('value', []))}\n")
    for item in result.get("value", []):
        print(f"  #{item['WorkItemId']}  Created: {item['CreatedDate'][:10]}  {item['Title']}")


asyncio.run(main())
```

**How it works**: `Filter.and_` combines multiple conditions. `Filter.ge` means "greater or equal" — works with ISO-format dates. `StateCategory` works in any language.

---

## 3. Paginate all items from a year

**When you need this**: analyze all work items created in 2025 — potentially thousands of records.

```python
"""Recipe 3: paginate all items from a year."""
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
org = os.environ.get("AZURE_DEVOPS_ORG") or ""
project = os.environ.get("AZURE_DEVOPS_PROJECT") or ""
pat = os.environ.get("AZURE_DEVOPS_PAT") or ""


async def main() -> None:
    from ado_odata_async import AdoODataClient
    from ado_odata_async.query import Filter

    total = 0
    async with AdoODataClient(org=org, project=project, pat=pat) as client:
        # paginate() handles pagination automatically
        async for page in client.paginate(
            "WorkItems",
            top=100,
            query={
                "$filter": "CreatedDate ge 2025-01-01 and CreatedDate lt 2026-01-01",
                "$select": "WorkItemId,Title,WorkItemType,CreatedDate",
                "$orderby": "WorkItemId asc",
            },
        ):
            items = page.get("value", [])
            total += len(items)
            print(f"Page received with {len(items)} items (running total: {total})")

    print(f"\nTotal work items in 2025: {total}")


asyncio.run(main())
```

**How it works**: `client.paginate()` controls `$skip` and `$top` automatically. When the server returns `@odata.nextLink`, the library follows that link. When there's no more data, the loop ends.

---

## 4. Calculate cycle time for closed items

**When you need this**: find out how long the team is taking to deliver — the most important flow metric.

```python
"""Recipe 4: calculate cycle time for closed items."""
import asyncio
from datetime import datetime
import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
org = os.environ.get("AZURE_DEVOPS_ORG") or ""
project = os.environ.get("AZURE_DEVOPS_PROJECT") or ""
pat = os.environ.get("AZURE_DEVOPS_PAT") or ""


def parse_date(val: str | None):
    if not val:
        return None
    try:
        # ISO 8601: Azure DevOps returns UTC dates as "2025-01-15T10:30:00Z"
        # .replace("Z", "+00:00") converts the Z suffix to Python-readable format
        return datetime.fromisoformat(val.replace("Z", "+00:00"))
    except Exception:
        return None


async def main() -> None:
    from ado_odata_async import AdoODataClient

    ciclo_dias = []
    async with AdoODataClient(org=org, project=project, pat=pat) as client:
        async for page in client.paginate(
            "WorkItems",
            top=200,
            query={
                "$filter": "StateCategory eq 'Completed'",
                "$select": "WorkItemId,Title,ActivatedDate,ClosedDate",
                "$orderby": "ClosedDate desc",
            },
        ):
            for item in page.get("value", []):
                ad = parse_date(item.get("ActivatedDate"))
                cd = parse_date(item.get("ClosedDate"))
                if ad and cd and cd > ad:
                    dias = (cd - ad).total_seconds() / 86400
                    if dias > 0:
                        ciclo_dias.append(dias)

    if not ciclo_dias:
        print("No items with cycle time available.")
        return

    ciclo_dias.sort()
    n = len(ciclo_dias)
    p50 = ciclo_dias[min(n - 1, int(n * 0.5))]
    p85 = ciclo_dias[min(n - 1, int(n * 0.85))]
    p95 = ciclo_dias[min(n - 1, int(n * 0.95))]

    print(f"Items analyzed: {n}")
    print(f"Cycle time p50:   {p50:.1f} days")
    print(f"Cycle time p85:   {p85:.1f} days")
    print(f"Cycle time p95:   {p95:.1f} days")


asyncio.run(main())
```

**Expected output**:
```
Items analyzed: 47
Cycle time p50:   3.2 days
Cycle time p85:   8.7 days
Cycle time p95:   14.1 days
```

**How it works**: We filter by `StateCategory eq 'Completed'` to get finished items. We calculate the difference between `ActivatedDate` (when work started) and `ClosedDate` (when it finished). We use percentiles (p50, p85, p95) instead of average because cycle time distribution is usually skewed.

> ⚠️ **Unbounded pagination**: `client.paginate()` iterates **indefinitely** while there's data in the API. For very large datasets (hundreds of thousands of records), consider adding a page counter or using `break` after a maximum. Example: `async for page in client.paginate(...): if page_count >= 50: break`.

---

## 5. Group by WorkItemType and count

**When you need this**: find out how many bugs, tasks, and stories exist in the project.

```python
"""Recipe 5: count work items by type."""
import asyncio
import os
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
org = os.environ.get("AZURE_DEVOPS_ORG") or ""
project = os.environ.get("AZURE_DEVOPS_PROJECT") or ""
pat = os.environ.get("AZURE_DEVOPS_PAT") or ""


async def main() -> None:
    from ado_odata_async import AdoODataClient

    contagem: Counter[str] = Counter()
    async with AdoODataClient(org=org, project=project, pat=pat) as client:
        async for page in client.paginate(
            "WorkItems",
            top=200,
            query={
                "$select": "WorkItemId,WorkItemType",
                "$orderby": "WorkItemId asc",
            },
        ):
            for item in page.get("value", []):
                contagem[item["WorkItemType"]] += 1

    print("Distribution by type:\n")
    for tipo, qtd in contagem.most_common():
        barra = "█" * min(qtd, 50)
        print(f"  {tipo:15s} {qtd:5d}  {barra}")


asyncio.run(main())
```

**Expected output**:
```
Distribution by type:

  Bug              23  █████████████████████
  Task             89  ██████████████████████████████████████████████████
  User Story       12  ████████████
```

**How it works**: We use `collections.Counter` to count each type. Pagination ensures we get all items in the project, not just the first 200. The `async for page in ...` loop consumes one page at a time.

---

## 6. Save results to CSV/JSON

**When you need this**: export data to open in Excel, analyze in pandas, or share with the team.

```python
"""Recipe 6: export work items to CSV and JSON."""
import asyncio
import csv
import json
import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
org = os.environ.get("AZURE_DEVOPS_ORG") or ""
project = os.environ.get("AZURE_DEVOPS_PROJECT") or ""
pat = os.environ.get("AZURE_DEVOPS_PAT") or ""


async def main() -> None:
    from ado_odata_async import AdoODataClient

    todos: list[dict] = []
    async with AdoODataClient(org=org, project=project, pat=pat) as client:
        async for page in client.paginate(
            "WorkItems",
            top=200,
            query={
                "$filter": "StateCategory eq 'Completed'",
                "$select": "WorkItemId,Title,WorkItemType,State,CreatedDate,ClosedDate",
                "$orderby": "ClosedDate desc",
            },
        ):
            todos.extend(page.get("value", []))

    # JSON
    with open("work_items.json", "w", encoding="utf-8") as f:
        json.dump(todos, f, indent=2, ensure_ascii=False, default=str)
    print(f"JSON saved: work_items.json ({len(todos)} records)")

    # CSV
    if todos:
        with open("work_items.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(todos[0].keys()))
            writer.writeheader()
            writer.writerows(todos)
        print(f"CSV saved: work_items.csv ({len(todos)} records)")


asyncio.run(main())
```

**Expected output**:
```
JSON saved: work_items.json (47 records)
CSV saved: work_items.csv (47 records)
```

**How it works**: We collect all items via pagination, then use `json.dump` and `csv.DictWriter` to export. The `ensure_ascii=False` parameter preserves accented characters. `default=str` converts dates to strings since JSON doesn't serialize `datetime` natively.

---

## 7. Handle authentication and network errors

**When you need this**: build a robust script that doesn't break if the PAT expired or the network failed.

```python
"""Recipe 7: robust error handling."""
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
org = os.environ.get("AZURE_DEVOPS_ORG") or ""
project = os.environ.get("AZURE_DEVOPS_PROJECT") or ""
pat = os.environ.get("AZURE_DEVOPS_PAT") or ""


async def main() -> None:
    from ado_odata_async import (
        AdoODataClient,
        AuthenticationError,
        BadRequestError,
        RateLimitError,
        TransientError,
    )
    from ado_odata_async.query import Filter

    if not pat or not org or not project:
        print("ERROR: credentials not found in .env")
        sys.exit(1)

    try:
        async with AdoODataClient(org=org, project=project, pat=pat) as client:
            result = await (
                client.query("WorkItems")
                .filter(Filter.eq("StateCategory", "Completed"))
                .select("WorkItemId", "Title")
                .top(5)
                .get()
            )

        for item in result.get("value", []):
            print(f"#{item['WorkItemId']}: {item['Title']}")

    except AuthenticationError:
        print("ERROR: invalid or expired PAT. Create a new token at")
        print("  https://dev.azure.com/{your-org}/_usersSettings/tokens")
        sys.exit(1)

    except BadRequestError as e:
        print(f"ERROR: invalid request — check the filter syntax")
        print(f"  Detail: {e}")
        sys.exit(1)

    except RateLimitError:
        print("ERROR: too many requests — wait a few minutes and try again")
        sys.exit(1)

    except TransientError:
        print("ERROR: temporary network or server issue — try again")
        sys.exit(1)


asyncio.run(main())
```

**How it works**: Each error type has a specific exception. `AuthenticationError` is for PAT issues (retrying won't help). `BadRequestError` is for malformed filters. `RateLimitError` and `TransientError` are temporary — the library already retries automatically with exponential backoff (up to 5 attempts), but if it still fails, the exception reaches you.

---

## 8. Use the Apply DSL with aggregate

**When you need this**: query `WorkItemSnapshot` or perform aggregations (counts, grouped sums).

> ⚠️ **Important**: Azure DevOps Analytics requires the `as <alias>` clause in aggregates. Without the alias (e.g., `aggregate($count as Count)`) — the server returns `400 Bad Request`. This library always generates the alias automatically.

```python
"""Recipe 8: apply $apply with groupby and aggregate."""
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
org = os.environ.get("AZURE_DEVOPS_ORG") or ""
project = os.environ.get("AZURE_DEVOPS_PROJECT") or ""
pat = os.environ.get("AZURE_DEVOPS_PAT") or ""


async def main() -> None:
    from ado_odata_async import AdoODataClient
    from ado_odata_async.query import Apply, Filter

    async with AdoODataClient(org=org, project=project, pat=pat) as client:
        # WorkItemSnapshot REQUIRES groupby with DateSK
        result = await (
            client.query("WorkItemSnapshot")
            .apply(
                Apply()
                .filter(Filter.eq("StateCategory", "Completed"))
                .groupby("DateSK", "State")
                .aggregate("$count", alias="Count")
            )
            .top(10)
            .get()
        )

    for row in result.get("value", []):
        print(f"Date: {row['DateSK']}  State: {row['State']:15s}  Count: {row.get('Count', 'N/A')}")


asyncio.run(main())
```

**Expected output**:
```
Date: 2025-05-01  State: Done           Count: 12
Date: 2025-05-01  State: Completed      Count: 5
Date: 2025-05-02  State: Done           Count: 8
```

**How it works**: `Apply` builds the expression `$apply=filter(...)/groupby((DateSK,State),aggregate($count as Count))`. The aggregate is **nested** inside the groupby (syntax required by ADO Analytics). `.aggregate("$count", alias="Count")` counts the rows in each group, and the alias `Count` names the output column.

### Understanding the output

Each row represents a date × state combination. `DateSK` is the date key in `YYYY-MM-DD` format (don't confuse with `DateValue`, used in `WorkItemBoardSnapshot`). `State` is the localized name (e.g., "Done", "Completed", "In Progress").

### Useful variations

```python
# Sum of effort (if your project fills in Effort)
Apply().groupby("WorkItemType").aggregate("Effort", "sum")

# Average size by type
Apply().groupby("WorkItemType").aggregate("StoryPoints", "average")

# Count of bugs by severity (use $count — countdistinct is blocked)
Apply().groupby("State", "Priority").aggregate("$count", alias="Count")
```

---

## Common mistakes

### 1. Reversed aggregate arguments

```python
# ❌ WRONG: method in the field position
Apply().groupby("State").aggregate("Sum", "Effort")

# ✅ CORRECT: field first, method second (lowercase)
Apply().groupby("State").aggregate("Effort", "sum")
```

The `aggregate(field, method)` method follows the canonical OData order: field/property first, aggregation method second. Valid methods: `sum`, `min`, `max`, `average` (always lowercase). For row counting, use the virtual field `$count` with `.aggregate("$count", alias="Name")`.

> ⚠️ **`countdistinct` is blocked**: Azure DevOps Analytics **does not support** `countdistinct` (the operation exists in OData, but the ADO service returns an error). Use `$count` inside `groupby`, or `sum`/`min`/`max`/`avg` on a numeric field. [Official documentation](https://learn.microsoft.com/en-us/azure/devops/report/extend-analytics/odata-query-guidelines?view=azure-devops).

### 2. Using `State` instead of `StateCategory` in filters

```python
# ❌ WRONG: State returns localized names (depends on project language)
filter_expr = Filter.eq("State", "Done")

# ✅ CORRETO: StateCategory works in any language
filter_expr = Filter.eq("StateCategory", "Completed")
```

### 3. Confusing `$filter` with `Apply.filter()`

```python
# ❌ WRONG: applying filter on QueryBuilder when it should be on Apply
client.query("WorkItemSnapshot").filter(...)  # generates $filter in URL — rejected by service

# ✅ CORRECT: use Apply.filter() inside the $apply expression
client.query("WorkItemSnapshot").apply(
    Apply().filter(Filter.eq("StateCategory", "Completed"))
)
```

`QueryBuilder.filter()` generates `$filter` in the URL. `Apply.filter()` generates `filter(...)` inside `$apply`. Mixing the two produces unexpected results — `$filter` is applied before aggregation, `$apply/filter` after.

---

## Português (Brasil)

[Português](#english) | **English**

# Cookbook: 8 receitas práticas

> Todas as receitas abaixo usam código testado e funcionam com dados reais do Azure DevOps.
> Presumem que as credenciais estão no `.env` conforme o [guia de início rápido](getting-started.md).

---

## 1. Listar os 10 work items criados mais recentemente

**Quando você precisa**: dar uma primeira olhada no que está acontecendo no projeto — ver os items mais recentes.

```python
"""Receita 1: listar work items mais recentes."""
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
org = os.environ.get("AZURE_DEVOPS_ORG") or ""
project = os.environ.get("AZURE_DEVOPS_PROJECT") or ""
pat = os.environ.get("AZURE_DEVOPS_PAT") or ""


async def main() -> None:
    from ado_odata_async import AdoODataClient
    from ado_odata_async.query import Filter

    async with AdoODataClient(org=org, project=project, pat=pat) as client:
        result = await (
            client.query("WorkItems")
            .select("WorkItemId", "Title", "WorkItemType", "State", "CreatedDate")
            .orderby("CreatedDate desc")
            .top(10)
            .get()
        )

    for item in result.get("value", []):
        print(f"#{item['WorkItemId']:6d}  [{item['WorkItemType']:10s}]  "
              f"{item['State']:15s}  {item['CreatedDate'][:10]}  {item['Title']}")


asyncio.run(main())
```

**Output esperado**:
```
#   42  [Tarefa    ]  Done             2025-05-20  Criar tela de login
#   43  [Bug       ]  Concluído        2025-05-19  Corrigir timeout
#  ...
```

**Como funciona**: `orderby("CreatedDate desc")` ordena do mais recente para o mais antigo. `top(10)` limita a 10 resultados. O `select` reduz a quantidade de dados trafegados.

---

## 2. Filtrar por estado e intervalo de datas

**Quando você precisa**: buscar bugs abertos das últimas duas semanas.

```python
"""Receita 2: filtrar bugs ativos das últimas 2 semanas."""
import asyncio
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
org = os.environ.get("AZURE_DEVOPS_ORG") or ""
project = os.environ.get("AZURE_DEVOPS_PROJECT") or ""
pat = os.environ.get("AZURE_DEVOPS_PAT") or ""

days_ago = (datetime.now(UTC) - timedelta(days=14)).isoformat()


async def main() -> None:
    from ado_odata_async import AdoODataClient
    from ado_odata_async.query import Filter

    filtro = Filter.and_(
        Filter.eq("WorkItemType", "Bug"),
        Filter.eq("StateCategory", "InProgress"),
        Filter.ge("CreatedDate", days_ago),
    )

    async with AdoODataClient(org=org, project=project, pat=pat) as client:
        result = await (
            client.query("WorkItems")
            .filter(filtro)
            .select("WorkItemId", "Title", "CreatedDate")
            .top(20)
            .get()
        )

    print(f"Bugs abertos nas últimas 2 semanas: {len(result.get('value', []))}\n")
    for item in result.get("value", []):
        print(f"  #{item['WorkItemId']}  Criado: {item['CreatedDate'][:10]}  {item['Title']}")


asyncio.run(main())
```

**Como funciona**: `Filter.and_` combina múltiplas condições. `Filter.ge` é "maior ou igual" (greater or equal) — funciona com dates em formato ISO. `StateCategory` funciona em qualquer idioma.

---

## 3. Paginar todos os items de um ano

**Quando você precisa**: analisar todos os work items criados em 2025 — potencialmente milhares de registros.

```python
"""Receita 3: paginar todos os items de um ano."""
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
org = os.environ.get("AZURE_DEVOPS_ORG") or ""
project = os.environ.get("AZURE_DEVOPS_PROJECT") or ""
pat = os.environ.get("AZURE_DEVOPS_PAT") or ""


async def main() -> None:
    from ado_odata_async import AdoODataClient
    from ado_odata_async.query import Filter

    total = 0
    async with AdoODataClient(org=org, project=project, pat=pat) as client:
        # O método paginate() lida com a paginação automaticamente
        async for page in client.paginate(
            "WorkItems",
            top=100,
            query={
                "$filter": "CreatedDate ge 2025-01-01 and CreatedDate lt 2026-01-01",
                "$select": "WorkItemId,Title,WorkItemType,CreatedDate",
                "$orderby": "WorkItemId asc",
            },
        ):
            items = page.get("value", [])
            total += len(items)
            print(f"Página recebida com {len(items)} items (total acumulado: {total})")

    print(f"\nTotal de work items em 2025: {total}")


asyncio.run(main())
```

**Como funciona**: `client.paginate()` controla automaticamente `$skip` e `$top`. Quando o servidor retorna `@odata.nextLink`, a biblioteca segue esse link. Quando não há mais dados, o loop termina.

---

## 4. Calcular cycle time de items fechados

**Quando você precisa**: saber quanto tempo o time está levando para entregar — a métrica mais importante de fluxo.

```python
"""Receita 4: calcular cycle time dos items fechados."""
import asyncio
from datetime import datetime
import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
org = os.environ.get("AZURE_DEVOPS_ORG") or ""
project = os.environ.get("AZURE_DEVOPS_PROJECT") or ""
pat = os.environ.get("AZURE_DEVOPS_PAT") or ""


def parse_date(val: str | None):
    if not val:
        return None
    try:
        # ISO 8601: o Azure DevOps retorna datas UTC no formato "2025-01-15T10:30:00Z"
        # O replace("Z", "+00:00") converte o sufixo Z para formato legível pelo Python
        return datetime.fromisoformat(val.replace("Z", "+00:00"))
    except Exception:
        return None


async def main() -> None:
    from ado_odata_async import AdoODataClient

    ciclo_dias = []
    async with AdoODataClient(org=org, project=project, pat=pat) as client:
        async for page in client.paginate(
            "WorkItems",
            top=200,
            query={
                "$filter": "StateCategory eq 'Completed'",
                "$select": "WorkItemId,Title,ActivatedDate,ClosedDate",
                "$orderby": "ClosedDate desc",
            },
        ):
            for item in page.get("value", []):
                ad = parse_date(item.get("ActivatedDate"))
                cd = parse_date(item.get("ClosedDate"))
                if ad and cd and cd > ad:
                    dias = (cd - ad).total_seconds() / 86400
                    if dias > 0:
                        ciclo_dias.append(dias)

    if not ciclo_dias:
        print("Nenhum item com cycle time disponível.")
        return

    ciclo_dias.sort()
    n = len(ciclo_dias)
    p50 = ciclo_dias[min(n - 1, int(n * 0.5))]
    p85 = ciclo_dias[min(n - 1, int(n * 0.85))]
    p95 = ciclo_dias[min(n - 1, int(n * 0.95))]

    print(f"Items analisados: {n}")
    print(f"Cycle time p50:   {p50:.1f} dias")
    print(f"Cycle time p85:   {p85:.1f} dias")
    print(f"Cycle time p95:   {p95:.1f} dias")


asyncio.run(main())
```

**Output esperado**:
```
Items analisados: 47
Cycle time p50:   3.2 dias
Cycle time p85:   8.7 dias
Cycle time p95:   14.1 dias
```

**Como funciona**: Filtramos por `StateCategory eq 'Completed'` para pegar items já finalizados. Calculamos a diferença entre `ActivatedDate` (quando começou) e `ClosedDate` (quando terminou). Usamos percentis (p50, p85, p95) em vez de média porque a distribuição de cycle time geralmente é assimétrica.

> ⚠️ **Paginação sem limite**: o `client.paginate()` itera **indefinidamente** enquanto houver dados na API. Para conjuntos muito grandes (centenas de milhares de registros), considere adicionar um contador de páginas ou usar `break` após um número máximo. Exemplo: `async for page in client.paginate(...): if page_count >= 50: break`.

---

## 5. Agrupar por WorkItemType e contar

**Quando você precisa**: saber quantos bugs, tarefas, histórias existem no projeto.

```python
"""Receita 5: contar work items por tipo."""
import asyncio
import os
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
org = os.environ.get("AZURE_DEVOPS_ORG") or ""
project = os.environ.get("AZURE_DEVOPS_PROJECT") or ""
pat = os.environ.get("AZURE_DEVOPS_PAT") or ""


async def main() -> None:
    from ado_odata_async import AdoODataClient

    contagem: Counter[str] = Counter()
    async with AdoODataClient(org=org, project=project, pat=pat) as client:
        async for page in client.paginate(
            "WorkItems",
            top=200,
            query={
                "$select": "WorkItemId,WorkItemType",
                "$orderby": "WorkItemId asc",
            },
        ):
            for item in page.get("value", []):
                contagem[item["WorkItemType"]] += 1

    print("Distribuição por tipo:\n")
    for tipo, qtd in contagem.most_common():
        barra = "█" * min(qtd, 50)
        print(f"  {tipo:15s} {qtd:5d}  {barra}")


asyncio.run(main())
```

**Output esperado**:
```
Distribuição por tipo:

  Bug              23  █████████████████████
  Tarefa           89  ██████████████████████████████████████████████████
  User Story       12  ████████████
```

**Como funciona**: Usamos `collections.Counter` para contar cada tipo. A paginação garante que pegamos todos os items do projeto, não só os 200 primeiros. O loop `async for page in ...` consome uma página por vez.

---

## 6. Salvar resultados em CSV/JSON

**Quando você precisa**: exportar dados para abrir no Excel, fazer análise em pandas ou compartilhar com o time.

```python
"""Receita 6: exportar work items para CSV e JSON."""
import asyncio
import csv
import json
import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
org = os.environ.get("AZURE_DEVOPS_ORG") or ""
project = os.environ.get("AZURE_DEVOPS_PROJECT") or ""
pat = os.environ.get("AZURE_DEVOPS_PAT") or ""


async def main() -> None:
    from ado_odata_async import AdoODataClient

    todos: list[dict] = []
    async with AdoODataClient(org=org, project=project, pat=pat) as client:
        async for page in client.paginate(
            "WorkItems",
            top=200,
            query={
                "$filter": "StateCategory eq 'Completed'",
                "$select": "WorkItemId,Title,WorkItemType,State,CreatedDate,ClosedDate",
                "$orderby": "ClosedDate desc",
            },
        ):
            todos.extend(page.get("value", []))

    # JSON
    with open("work_items.json", "w", encoding="utf-8") as f:
        json.dump(todos, f, indent=2, ensure_ascii=False, default=str)
    print(f"JSON salvo: work_items.json ({len(todos)} registros)")

    # CSV
    if todos:
        with open("work_items.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(todos[0].keys()))
            writer.writeheader()
            writer.writerows(todos)
        print(f"CSV salvo: work_items.csv ({len(todos)} registros)")


asyncio.run(main())
```

**Output esperado**:
```
JSON salvo: work_items.json (47 registros)
CSV salvo: work_items.csv (47 registros)
```

**Como funciona**: Coletamos todos os items via paginação, depois usamos `json.dump` e `csv.DictWriter` para exportar. O parâmetro `ensure_ascii=False` preserva caracteres acentuados (PT-BR). `default=str` converte datas para string, já que o JSON não serializa `datetime` nativamente.

---

## 7. Tratar erros de autenticação e rede

**Quando você precisa**: fazer um script robusto que não quebre se o PAT expirou ou a rede falhar.

```python
"""Receita 7: tratamento robusto de erros."""
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
org = os.environ.get("AZURE_DEVOPS_ORG") or ""
project = os.environ.get("AZURE_DEVOPS_PROJECT") or ""
pat = os.environ.get("AZURE_DEVOPS_PAT") or ""


async def main() -> None:
    from ado_odata_async import (
        AdoODataClient,
        AuthenticationError,
        BadRequestError,
        RateLimitError,
        TransientError,
    )
    from ado_odata_async.query import Filter

    if not pat or not org or not project:
        print("ERRO: credenciais não encontradas no .env")
        sys.exit(1)

    try:
        async with AdoODataClient(org=org, project=project, pat=pat) as client:
            result = await (
                client.query("WorkItems")
                .filter(Filter.eq("StateCategory", "Completed"))
                .select("WorkItemId", "Title")
                .top(5)
                .get()
            )

        for item in result.get("value", []):
            print(f"#{item['WorkItemId']}: {item['Title']}")

    except AuthenticationError:
        print("ERRO: PAT inválido ou expirado. Crie um novo token em ")
        print("  https://dev.azure.com/{sua-org}/_usersSettings/tokens")
        sys.exit(1)

    except BadRequestError as e:
        print(f"ERRO: requisição inválida — verifique a sintaxe do filtro")
        print(f"  Detalhe: {e}")
        sys.exit(1)

    except RateLimitError:
        print("ERRO: muitas requisições — aguarde alguns minutos e tente novamente")
        sys.exit(1)

    except TransientError:
        print("ERRO: problema temporário de rede ou servidor — tente novamente")
        sys.exit(1)


asyncio.run(main())
```

**Como funciona**: Cada tipo de erro tem uma exceção específica. `AuthenticationError` é para problemas de PAT (não adianta repetir). `BadRequestError` é para filtros mal-formados. `RateLimitError` e `TransientError` são temporários — a própria biblioteca já tenta repetir automaticamente com backoff exponencial (até 5 tentativas), mas se mesmo assim falhar, a exceção chega até você.

---

## 8. Usar Apply DSL com aggregate

**Quando você precisa**: consultar `WorkItemSnapshot` ou fazer agregações (contagens, somas agrupadas).

> ⚠️ **Importante**: o Azure DevOps Analytics exige a cláusula `as <alias>` no aggregate. Sem o alias (ex.: `aggregate($count as Count)`) — o servidor retorna `400 Bad Request`. Esta biblioteca sempre gera o alias automaticamente.

```python
"""Receita 8: aplicar $apply com groupby e aggregate."""
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
org = os.environ.get("AZURE_DEVOPS_ORG") or ""
project = os.environ.get("AZURE_DEVOPS_PROJECT") or ""
pat = os.environ.get("AZURE_DEVOPS_PAT") or ""


async def main() -> None:
    from ado_odata_async import AdoODataClient
    from ado_odata_async.query import Apply, Filter

    async with AdoODataClient(org=org, project=project, pat=pat) as client:
        # WorkItemSnapshot REQUER groupby com DateSK
        result = await (
            client.query("WorkItemSnapshot")
            .apply(
                Apply()
                .filter(Filter.eq("StateCategory", "Completed"))
                .groupby("DateSK", "State")
                .aggregate("$count", alias="Count")
            )
            .top(10)
            .get()
        )

    for row in result.get("value", []):
        print(f"Data: {row['DateSK']}  Estado: {row['State']:15s}  Qtd: {row.get('Count', 'N/A')}")


asyncio.run(main())
```

**Output esperado**:
```
Data: 2025-05-01  Estado: Concluído      Qtd: 12
Data: 2025-05-01  Estado: Done           Qtd: 5
Data: 2025-05-02  Estado: Concluído      Qtd: 8
```

**Como funciona**: O `Apply` monta a expressão `$apply=filter(...)/groupby((DateSK,State),aggregate($count as Count))`. O aggregate é **aninhado** dentro do groupby (sintaxe exigida pelo ADO Analytics). O `.aggregate("$count", alias="Count")` conta as linhas de cada grupo, e o alias `Count` nomeia a coluna de saída.

### Entendendo a saída

Cada linha representa uma combinação de data × estado. `DateSK` é a chave da data no formato `YYYY-MM-DD` (não confundir com `DateValue`, que é usada no `WorkItemBoardSnapshot`). `State` é o nome localizado (ex.: "Concluído", "Done", "In Progress").

### Variações úteis

```python
# Soma de esforço (se seu projeto preencher Effort)
Apply().groupby("WorkItemType").aggregate("Effort", "sum")

# Média de tamanho por tipo
Apply().groupby("WorkItemType").aggregate("StoryPoints", "average")

# Contagem de bugs por severidade (use $count — countdistinct é bloqueado)
Apply().groupby("State", "Priority").aggregate("$count", alias="Count")
```

---

## Erros comuns

### 1. Ordem invertida no aggregate

```python
# ❌ ERRADO: método na posição do campo
Apply().groupby("State").aggregate("Sum", "Effort")

# ✅ CORRETO: campo primeiro, método em segundo (minúsculas)
Apply().groupby("State").aggregate("Effort", "sum")
```

O método `aggregate(field, method)`) segue a ordem canônica do OData: campo/propriedade primeiro, método de agregação depois. Métodos válidos: `sum`, `min`, `max`, `average` (sempre minúsculas). Para contagem de linhas, use o campo virtual `$count` com `.aggregate("$count", alias="Nome")`.

> ⚠️ **`countdistinct` é bloqueado**: O Azure DevOps Analytics **não suporta** `countdistinct` (a operação existe no OData, mas o serviço ADO retorna erro). Use `$count` dentro de `groupby`, ou `sum`/`min`/`max`/`avg` em um campo numérico. [Documentação oficial](https://learn.microsoft.com/en-us/azure/devops/report/extend-analytics/odata-query-guidelines?view=azure-devops).

### 2. Usar `State` em vez de `StateCategory` em filtros

```python
# ❌ ERRADO: State retorna nomes localizados (depende do idioma do projeto)
filter_expr = Filter.eq("State", "Concluído")

# ✅ CORRETO: StateCategory funciona em qualquer idioma
filter_expr = Filter.eq("StateCategory", "Completed")
```

### 3. Confundir `$filter` com `Apply.filter()`

```python
# ❌ ERRADO: aplicar filtro no QueryBuilder quando deveria ser no Apply
client.query("WorkItemSnapshot").filter(...)  # gera $filter na URL — rejeitado pelo serviço

# ✅ CORRETO: use Apply.filter() dentro da expressão $apply
client.query("WorkItemSnapshot").apply(
    Apply().filter(Filter.eq("StateCategory", "Completed"))
)
```

O `QueryBuilder.filter()` gera `$filter` na URL. O `Apply.filter()` gera `filter(...)` dentro de `$apply`. Misturar os dois gera resultados inesperados — `$filter` é aplicado antes da agregação, `$apply/filter` depois.
