**English** | [Português](#português-brasil)

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
- [Flow Metrics & Delivery Analytics](#flow-metrics--delivery-analytics)
- [Docs index](#docs-index)
- [Troubleshooting](#troubleshooting)
- [License](#license)
- [Contributing](#contributing)
- [Acknowledgments](#acknowledgments)

---

## Overview

This library wraps the Azure DevOps Analytics OData API — eliminates raw URL construction, handles auth, pagination, retry, and the `$apply` [DSL](docs/glossary.md#apply). For you if you need [cycle time](docs/glossary.md#cycle-time-tempo-de-ciclo), [throughput](docs/glossary.md#throughput-vazo), or [WIP](docs/glossary.md#wip-work-in-progress) from Azure Boards without writing raw OData URLs.

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

## Flow Metrics & Delivery Analytics

Beyond raw OData queries, the library provides compute functions for delivery analytics. These functions work on data you have already fetched (e.g. via `client.get()` or `paginate()`).

### Plan History — `compute_plan_history`

```python
from ado_odata_async import compute_plan_history

items = [
    {"CreatedDate": "2025-01-10", "StateCategory": "Completed",
     "TargetDate": "2025-06-30", "CompletedDate": "2025-06-15"},
    {"CreatedDate": "2025-02-01", "StateCategory": "InProgress",
     "TargetDate": None, "CompletedDate": None},
]

result = compute_plan_history(items)
print(result.created_date)       # 2025-01-10
print(result.oldest_card_date)   # 2025-02-01
print(result.on_time_rate)       # 1.0
```

`PlanHistoryResult` has three fields:
- `created_date` — earliest `CreatedDate` across all items
- `oldest_card_date` — earliest `CreatedDate` among active (non-Completed) items, or `None`
- `on_time_rate` — fraction of completed items with a `TargetDate` that finished on or before target (0.0 to 1.0)

### Baseline — `compute_baseline_metrics`

Detects replanning by examining `TargetDate` changes across revision history:

```python
from ado_odata_async import compute_baseline_metrics

revisions = [
    {"TargetDate": "2025-06-30"},
    {"TargetDate": "2025-07-15"},
    {"TargetDate": "2025-07-15"},
]

result = compute_baseline_metrics(revisions)
print(result.original_target_date)  # "2025-06-30"
print(result.target_date_changes)   # 1
print(result.replanned)             # True
```

`BaselineResult` has three fields:
- `original_target_date` — first `TargetDate` value in chronological order, or `None`
- `target_date_changes` — count of changes between consecutive revisions
- `replanned` — `True` when `target_date_changes > 0`

### Flow Times — `compute_flow_times`

Calculates queue time and progress time from revision history:

```python
from ado_odata_async import compute_flow_times

revisions = [
    {"State": "New", "ChangedDate": "2025-01-10"},
    {"State": "Active", "ChangedDate": "2025-01-15"},
    {"State": "Resolved", "ChangedDate": "2025-01-20"},
    {"State": "Closed", "ChangedDate": "2025-01-22"},
]

result = compute_flow_times(revisions)
print(result.time_in_queue_days)      # 5
print(result.time_in_progress_days)   # 5
print(result.state_history[0])        # ("New", date(2025, 1, 10))
```

`FlowTimeResult` has three fields:
- `state_history` — sorted list of `(State, ChangedDate)` tuples
- `time_in_queue_days` — days from creation to first active state, or `None`
- `time_in_progress_days` — total days spent in active states

Active states recognized: `["Active", "In Progress", "Committed", "Design"]`.

### Child Count — `compute_child_count`

Counts direct children per parent from `WorkItemLinks` data:

```python
from ado_odata_async import compute_child_count

links = [
    {"SourceWorkItemId": 100, "TargetWorkItemId": 101},
    {"SourceWorkItemId": 100, "TargetWorkItemId": 102},
]

counts = compute_child_count(links)
print(counts)  # {100: 2}
```

### Hierarchy Depth — `compute_hierarchy_depth`

Computes depth from root for each node in a hierarchy DAG:

```python
from ado_odata_async import compute_hierarchy_depth

links = [
    {"SourceWorkItemId": 10, "TargetWorkItemId": 11},
    {"SourceWorkItemId": 11, "TargetWorkItemId": 12},
]

depth = compute_hierarchy_depth(links)
print(depth)  # {10: 0, 11: 1, 12: 2}
```

Root nodes (those never referenced as a target) get depth 0. Depth is capped at 100.

### Dependency Links — `fetch_dependency_links`

Fetches dependency links for a set of work items and builds a dependency map:

```python
import asyncio
from ado_odata_async import AdoODataClient, fetch_dependency_links

async def main() -> None:
    async with AdoODataClient(
        org="myorg", project="myproject", pat="your-pat"
    ) as client:
        deps = await fetch_dependency_links(
            client,
            [100, 101, 102],
            resolve_titles=True,
            flag_overdue=True,
        )
        for wid, entry in deps.items():
            print(f"WorkItem {wid}:")
            print(f"  depends_on: {entry['depends_on']}")
            print(f"  blocks:      {entry['blocks']}")
            print(f"  risk_flags:  {entry['risk_flags']}")

asyncio.run(main())
```

The returned dict maps each work item ID to `{"depends_on": [...], "blocks": [...], "risk_flags": [...]}`. Optional parameters `resolve_titles` and `flag_overdue` enrich the output with titles and overdue flags.

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

---

<a id="english"></a>

## Português (Brasil)

[Português](#english) | **English**

Cliente Python assíncrono para Azure DevOps Analytics OData.

[![License: MPL 2.0](https://img.shields.io/badge/license-MPL%202.0-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](pyproject.toml)

---

## Índice

- [Visão geral](#visão-geral)
- [Funcionalidades](#funcionalidades)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Início rápido](#início-rápido)
- [Exemplo de saída](#exemplo-de-saída)
- [Uso](#uso)
- [Métricas de Fluxo e Análise de Entrega](#métricas-de-fluxo-e-análise-de-entrega)
- [Índice da documentação](#índice-da-documentação)
- [Solução de problemas](#solução-de-problemas)
- [Licença](#licença)
- [Contribuindo](#contribuindo)
- [Agradecimentos](#agradecimentos)

---

## Visão geral

Esta biblioteca encapsula a API OData do Azure DevOps Analytics — elimina a construção manual de URLs, cuida de autenticação, paginação, retentativas e da DSL `$apply`. Para você se precisar de [cycle time](docs/glossary.md#cycle-time-tempo-de-ciclo), [throughput](docs/glossary.md#throughput-vazo) ou [WIP](docs/glossary.md#wip-work-in-progress) do Azure Boards sem escrever URLs OData na unha.

---

## Funcionalidades

- **Assíncrono por padrão** — construído sobre `aiohttp`, sem chamadas bloqueantes
- **DSL `$apply`** — encadeie `filter()`, `groupby()`, `aggregate()` sem strings OData cruas
- **Paginação** — tratamento automático de `@odata.nextLink` via `paginate()`
- **Retentativas com backoff** — retentativas baseadas em `tenacity` para falhas transitórias
- **Validação com Pydantic** — modelos estritos e imutáveis para todas as respostas
- **Sem dependências externas de auth** — usa `aiohttp.BasicAuth` direto com seu PAT

---

## Pré-requisitos

- **Python 3.12+**
- **Gerenciador de pacotes [uv](https://docs.astral.sh/uv/)** — instale com `pip install uv` ou visite o link
- **Personal Access Token do Azure DevOps** com os escopos:
  - `Work Items (Read)`
  - `Analytics (Read)`
- **Nome da organização** (ex.: `myorg`) e **nome do projeto** (ex.: `myproject`) da sua URL do Azure DevOps

---

## Instalação

**Do git:**

```bash
uv add git+https://github.com/fcoalcantarajr/odata-python-wrapper@main
```

**Desenvolvimento local:**

```bash
git clone https://github.com/fcoalcantarajr/odata-python-wrapper.git
cd odata-python-wrapper
uv sync
```

---

## Configuração

Crie um arquivo `.env` na raiz do seu projeto com estas três variáveis:

```
AZURE_DEVOPS_ORG=your-org-name
AZURE_DEVOPS_PROJECT=your-project-name
AZURE_DEVOPS_PAT=your-personal-access-token
```

Substitua `your-org-name`, `your-project-name` e `your-personal-access-token` pelos seus valores reais do Azure DevOps.

**Segurança do PAT:** Use escopos mínimos (apenas Work Items Read + Analytics Read), defina uma expiração curta (30 dias) e nunca faça commit do `.env` no controle de versão.

---

## Início rápido

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

Salve o script como `quickstart.py` e execute:

```bash
uv run python quickstart.py
```

---

## Exemplo de saída

O quickstart filtra por `StateCategory eq 'Completed'` e agrupa por `State`. No Azure DevOps, a categoria Completed inclui estados como Closed, Done e Removed:

```
Closed               158
Done                 42
Removed               3
```

---

## Uso

**Seleção simples com top:**

```python
result = await (
    client.query("WorkItems")
    .select("WorkItemId", "Title", "State")
    .top(5)
    .get()
)
```

**Paginação para grandes volumes de dados:**

Use o método `paginate()` para tratar automaticamente os tokens de continuação `@odata.nextLink`:

```python
async for page in client.query("WorkItems").select("WorkItemId", "Title").paginate():
    for item in page.get("value", []):
        print(item["WorkItemId"], item["Title"])
```

---

## Métricas de Fluxo e Análise de Entrega

Além das consultas OData diretas, a biblioteca oferece funções de análise para métricas de entrega. Estas funções processam dados que você já obteve (ex.: via `client.get()` ou `paginate()`).

### Plan History — `compute_plan_history`

```python
from ado_odata_async import compute_plan_history

items = [
    {"CreatedDate": "2025-01-10", "StateCategory": "Completed",
     "TargetDate": "2025-06-30", "CompletedDate": "2025-06-15"},
    {"CreatedDate": "2025-02-01", "StateCategory": "InProgress",
     "TargetDate": None, "CompletedDate": None},
]

result = compute_plan_history(items)
print(result.created_date)       # 2025-01-10
print(result.oldest_card_date)   # 2025-02-01
print(result.on_time_rate)       # 1.0
```

`PlanHistoryResult` tem três campos:
- `created_date` — `CreatedDate` mais antiga entre todos os itens
- `oldest_card_date` — `CreatedDate` mais antiga entre itens ativos (não-Completed), ou `None`
- `on_time_rate` — fração de itens concluídos com `TargetDate` que terminaram dentro ou antes do prazo (0.0 a 1.0)

### Baseline — `compute_baseline_metrics`

Detecta replanejamento examinando mudanças de `TargetDate` no histórico de revisões:

```python
from ado_odata_async import compute_baseline_metrics

revisions = [
    {"TargetDate": "2025-06-30"},
    {"TargetDate": "2025-07-15"},
    {"TargetDate": "2025-07-15"},
]

result = compute_baseline_metrics(revisions)
print(result.original_target_date)  # "2025-06-30"
print(result.target_date_changes)   # 1
print(result.replanned)             # True
```

`BaselineResult` tem três campos:
- `original_target_date` — primeiro valor de `TargetDate` em ordem cronológica, ou `None`
- `target_date_changes` — quantidade de mudanças entre revisões consecutivas
- `replanned` — `True` quando `target_date_changes > 0`

### Flow Times — `compute_flow_times`

Calcula tempo de fila e tempo em progresso a partir do histórico de revisões:

```python
from ado_odata_async import compute_flow_times

revisions = [
    {"State": "New", "ChangedDate": "2025-01-10"},
    {"State": "Active", "ChangedDate": "2025-01-15"},
    {"State": "Resolved", "ChangedDate": "2025-01-20"},
    {"State": "Closed", "ChangedDate": "2025-01-22"},
]

result = compute_flow_times(revisions)
print(result.time_in_queue_days)      # 5
print(result.time_in_progress_days)   # 5
print(result.state_history[0])        # ("New", date(2025, 1, 10))
```

`FlowTimeResult` tem três campos:
- `state_history` — lista ordenada de tuplas `(State, ChangedDate)`
- `time_in_queue_days` — dias da criação até o primeiro estado ativo, ou `None`
- `time_in_progress_days` — total de dias em estados ativos

Estados ativos reconhecidos: `["Active", "In Progress", "Committed", "Design"]`.

### Child Count — `compute_child_count`

Conta filhos diretos por pai a partir de dados `WorkItemLinks`:

```python
from ado_odata_async import compute_child_count

links = [
    {"SourceWorkItemId": 100, "TargetWorkItemId": 101},
    {"SourceWorkItemId": 100, "TargetWorkItemId": 102},
]

counts = compute_child_count(links)
print(counts)  # {100: 2}
```

### Hierarchy Depth — `compute_hierarchy_depth`

Calcula a profundidade a partir da raiz para cada nó em um DAG de hierarquia:

```python
from ado_odata_async import compute_hierarchy_depth

links = [
    {"SourceWorkItemId": 10, "TargetWorkItemId": 11},
    {"SourceWorkItemId": 11, "TargetWorkItemId": 12},
]

depth = compute_hierarchy_depth(links)
print(depth)  # {10: 0, 11: 1, 12: 2}
```

Nós raiz (que nunca aparecem como alvo) recebem profundidade 0. A profundidade máxima é 100.

### Dependency Links — `fetch_dependency_links`

Obtém links de dependência para um conjunto de work items e monta um mapa de dependências:

```python
import asyncio
from ado_odata_async import AdoODataClient, fetch_dependency_links

async def main() -> None:
    async with AdoODataClient(
        org="myorg", project="myproject", pat="your-pat"
    ) as client:
        deps = await fetch_dependency_links(
            client,
            [100, 101, 102],
            resolve_titles=True,
            flag_overdue=True,
        )
        for wid, entry in deps.items():
            print(f"WorkItem {wid}:")
            print(f"  depends_on: {entry['depends_on']}")
            print(f"  blocks:      {entry['blocks']}")
            print(f"  risk_flags:  {entry['risk_flags']}")

asyncio.run(main())
```

O dicionário retornado mapeia cada ID de work item para `{"depends_on": [...], "blocks": [...], "risk_flags": [...]}`. Os parâmetros opcionais `resolve_titles` e `flag_overdue` enriquecem a saída com títulos e flags de atraso.

---

## Índice da documentação

| Doc | O que tem dentro | Abra quando… |
|---|---|---|
| [getting-started.md](docs/getting-started.md) | Passo a passo de instalação, criação do PAT, configuração do .env | Você está começando do zero |
| [concepts.md](docs/concepts.md) | OData explicado, WorkItems vs Revisions vs Snapshot | Você quer entender a biblioteca |
| [cookbook.md](docs/cookbook.md) | 8 receitas: filtro, paginação, cycle time, exportação CSV | Você já conhece o básico |
| [glossary.md](docs/glossary.md) | Referência alfabética de termos | Você encontrou um termo que não conhece |
| [troubleshooting.md](docs/troubleshooting.md) | Sintoma → causa → solução para erros | Algo não está funcionando |
| [architecture.md](docs/architecture.md) | Camadas internas: Auth → HTTP → Client → Query → Serializer | Você quer entender como o código está organizado |
| [decisions.md](docs/decisions.md) | Architecture Decision Records (ADRs) | Você quer saber por que certas decisões de design foram tomadas |
| [intern_first_query.py](examples/intern_first_query.py) | Exemplo mínimo executável (usa `python-dotenv` se disponível) | Você quer o menor script possível |

---

## Solução de problemas

Veja [troubleshooting.md](docs/troubleshooting.md) para tabelas completas de sintoma → causa → solução.

**As 2 principais pegadinhas:**

1. **HTTP 203 = PAT inválido.** O ADO retorna 203 com `text/html` quando o PAT está expirado ou malformado. Isso não é retentável — regenere o token.

2. **`$apply` plano vs aninhado.** A biblioteca cuida da ordenação das cláusulas `$apply` automaticamente, mas seu `filter()` precisa vir antes do `groupby()` — filtros dentro de `$apply` escopam as linhas antes da agregação.

---

## Licença

Licenciada sob a Mozilla Public License 2.0. Veja [LICENSE](LICENSE) para detalhes. Você pode usar esta biblioteca como dependência em qualquer projeto; alterações nos arquivos da própria biblioteca precisam permanecer sob MPL-2.0.

---

## Contribuindo

Contribuições são bem-vindas! Abra uma issue ou envie um pull request. Rode `uv run pytest` e `uv run ruff check .` antes de enviar.

---

## Agradecimentos

Construído com [OhMyOpenCode](https://ohmyopencode.com)
