<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# Cookbook: 12 worked examples

## 1. Client setup

```python
import asyncio
from ado_odata_async import AdoODataClient

async def main() -> None:
    async with AdoODataClient(
        org="myorg",
        project="myproject",
        pat="your-personal-access-token",
    ) as client:
        # use client here
        pass

asyncio.run(main())
```

PAT must have "Analytics (read)" scope. Username is always empty (HR-8 gotcha 1).

## 2. Simple query with builder

```python
from ado_odata_async import AdoODataClient
from ado_odata_async.query import Filter

async with AdoODataClient(org="myorg", project="myproject", pat="...") as client:
    result = await (
        client.query("WorkItems")
        .filter(Filter.eq("State", "Active"))
        .select("WorkItemId", "Title", "State")
        .top(10)
        .get()
    )
    for item in result["value"]:
        print(item["WorkItemId"], item["Title"])
```

## 3. Complex filter with and/or/not

```python
filter_expr = Filter.or_(
    Filter.and_(
        Filter.eq("State", "Active"),
        Filter.eq("WorkItemType", "Bug"),
    ),
    Filter.and_(
        Filter.eq("State", "Resolved"),
        Filter.eq("WorkItemType", "Bug"),
    ),
)
# (State eq 'Active' and WorkItemType eq 'Bug') or (State eq 'Resolved' and WorkItemType eq 'Bug')
```

## 4. Ordering and skipping

```python
builder = (
    client.query("WorkItems")
    .filter(Filter.eq("WorkItemType", "Task"))
    .orderby("CreatedDate desc")
    .select("WorkItemId", "Title", "CreatedDate")
    .skip(20)
    .top(10)
)
print(str(builder))
# $filter=WorkItemType%20eq%20%27Task%27&$orderby=CreatedDate%20desc&$select=WorkItemId%2CTitle%2CCreatedDate&$skip=20&$top=10

result = await builder.get()
```

## 5. Apply DSL for WorkItemSnapshot

WorkItemSnapshot requires `$apply` with `groupby` (HR-13 gotcha 4):

```python
from ado_odata_async.query import Apply

apply_expr = (
    Apply()
    .filter(Filter.eq("State", "Active"))
    .groupby("DateSK", "State")
    .aggregate("Count", "WorkItemId")
)

result = await (
    client.query("WorkItemSnapshot")
    .apply(apply_expr)
    .top(10)
    .get()
)
```

## 6. Pagination

```python
async for page in client.paginate(
    "WorkItems",
    top=50,
    query={"$filter": "WorkItemType eq 'Bug'", "$select": "WorkItemId,Title"},
):
    print(f"Page with {len(page['value'])} items")
    for item in page["value"]:
        print(f"  {item['WorkItemId']}: {item['Title']}")
```

Using the builder:

```python
async for page in (
    client.query("WorkItems")
    .filter(Filter.eq("WorkItemType", "Bug"))
    .select("WorkItemId", "Title")
    .paginate(top=50)
):
    print(f"Page with {len(page['value'])} items")
```

## 7. Fetch single WorkItem by ID

```python
from ado_odata_async import AdoODataClient, WorkItem

async with AdoODataClient(org="myorg", project="myproject", pat="...") as client:
    try:
        wi = await client.get_workitem(42)
        print(f"#{wi.WorkItemId}: {wi.Title} ({wi.WorkItemType})")
    except IndexError:
        print("WorkItem 42 not found")
```

## 8. Error handling with typed exceptions

```python
from ado_odata_async import (
    AdoODataClient,
    AuthenticationError,
    BadRequestError,
    RateLimitError,
    TransientError,
)

async with AdoODataClient(org="myorg", project="myproject", pat="...") as client:
    try:
        result = await client.get("WorkItems", **{"$filter": "invalid syntax"})
    except AuthenticationError:
        print("PAT inválido ou expirado — verifique seu token")
    except BadRequestError as e:
        print(f"Erro na query: {e}")
    except RateLimitError:
        print("Rate limit excedido — tente novamente mais tarde")
    except TransientError:
        print("Erro transitório do servidor")
```

## 9. Using expand (WorkItemRevisions)

`$expand=Revisions` é bloqueado (HR-14 gotcha 5). Use entity set `WorkItemRevisions`:

```python
result = await (
    client.query("WorkItemRevisions")
    .filter(Filter.eq("WorkItemId", 42))
    .select("WorkItemId", "RevisedDate", "Title")
    .top(5)
    .get()
)
for rev in result["value"]:
    print(rev["RevisedDate"], rev["Title"])
```

## 10. Builder immutability

Builders são imutáveis — cada chain cria uma nova instância:

```python
base = client.query("WorkItems").filter(Filter.eq("WorkItemType", "Bug"))

active_bugs = base.filter(Filter.eq("State", "Active"))
resolved_bugs = base.filter(Filter.eq("State", "Resolved"))

assert str(base) != str(active_bugs)  # base não foi mutado
print(str(active_bugs))
# $filter=(WorkItemType eq 'Bug' and State eq 'Active')
```

## 11. Serialized URL and repr for debugging

Útil para debug ou logging:

```python
builder = (
    client.query("WorkItems")
    .apply(Apply().groupby("State").aggregate("Count", "WorkItemId"))
    .filter(Filter.eq("WorkItemType", "Bug"))
    .top(100)
)

# Human-readable repr
print(repr(builder))
# QueryBuilder(entity_set='WorkItems', clauses=[$apply="groupby((State))/aggregate(Count with WorkItemId)", $filter="WorkItemType eq 'Bug'", $top="100"])

# URL-encoded query string
url = str(builder)
# $apply=groupby((State))/aggregate(Count with WorkItemId)&$filter=WorkItemType%20eq%20%27Bug%27&$top=100
```

## 12. Retry behavior

A retry strategy é ativada automaticamente para erros transitórios e rate limit:

```python
from ado_odata_async import TransientError, RateLimitError

async with AdoODataClient(org="myorg", project="myproject", pat="...") as client:
    # Tentativas automáticas em caso de 429 (RateLimitError) ou 503 (TransientError)
    # Strategy: exponential backoff com jitter (1s → 60s max), até 5 retries
    result = await client.get("WorkItems", **{"$top": 10})
```

Para ver logs das tentativas de retry:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
# DEBUG:ado_odata_async.retry:Retry attempt 1/5 after 1.2s (HTTP 429)
```

## 13. Batch POST for long URLs

URLs que excedem 3000 caracteres são automaticamente convertidas para `POST $batch` (HR-10, gotcha 3). Configurável via `batch_threshold`:

```python
# Default: URLs > 3000 chars viram batch
async with AdoODataClient(org="myorg", project="myproject", pat="...") as client:
    result = await (
        client.query("WorkItems")
        .filter(
            Filter.eq("State", "Active"),
        )
        .select("WorkItemId", "Title", "State", "AssignedTo", "CreatedDate", "Tags")
        .orderby("CreatedDate desc")
        .top(100)
        .get()
    )
    # Se URL exceder batch_threshold, o client envia POST $batch
    # automaticamente com multipart/mixed

# Threshold customizado
async with AdoODataClient(
    org="myorg", project="myproject", pat="...", batch_threshold=2000
) as client:
    # URLs > 2000 chars viram batch
    ...
```

Veja [`docs/architecture.md`](architecture.md) para detalhes do fluxo batch.
