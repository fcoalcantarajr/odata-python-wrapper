**English** | [Português](#português-brasil)

# Core concepts

> Audience: CS intern (knows variables/loops/functions, never seen async/await, OData, or REST).

This document explains the concepts you need to understand to use `ado-odata-async` with confidence.

---

## What is OData?

OData (Open Data Protocol) is a standard that lets you query data through URLs — like a database accessible from the web.

**Analogy**: Imagine Azure DevOps as a giant Excel file. OData is like a "query" you type in the address bar to fetch only the rows and columns you need.

In practice, you build a URL with special parameters:

```
https://analytics.dev.azure.com/my-org/my-project/_odata/v4.0-preview/WorkItems?$top=10&$select=WorkItemId,Title,State&$filter=WorkItemType eq 'Bug'
```

| Parameter | Meaning | Example |
|---|---|---|
| `$filter` | Filters rows (like SQL WHERE) | `State eq 'Active'` |
| `$select` | Picks columns (like SELECT) | `WorkItemId,Title` |
| `$top` | Limits results | `$top=10` |
| `$orderby` | Sorts | `CreatedDate desc` |
| `$skip` | Skips rows (for pagination) | `$skip=20` |
| `$expand` | Fetches related data | `$expand=Children` |
| `$apply` | Groups and aggregates (like GROUP BY) | `groupby((State),aggregate($count as Count))` |

The `ado-odata-async` library builds these URLs for you using the `QueryBuilder` — you don't need to worry about the exact syntax.

---

## Azure DevOps: WorkItems, WorkItemRevisions, and WorkItemSnapshot

Azure Boards exposes three different views of the data. Picking the right one is essential.

### WorkItems

The **current** state of each work item. One row per item.

**When to use**: to see what's open now, who's assigned, current status.

```python
result = await (
    client.query("WorkItems")
    .select("WorkItemId", "Title", "State", "AssignedTo")
    .top(10)
    .get()
)
```

### WorkItemRevisions

The **complete history** of all changes. Every time someone edits a work item, a new revision is created.

**When to use**: for auditing, to find out who changed what and when.

```python
result = await (
    client.query("WorkItemRevisions")
    .filter(Filter.eq("WorkItemId", 42))
    .select("WorkItemId", "Title", "RevisedDate", "State")
    .get()
)
```

> **WARNING**: `$expand=Revisions` **does not work** in Analytics OData (it's blocked by the service). Always use the `WorkItemRevisions` entity set directly.

### WorkItemSnapshot

A daily "snapshot": one row per work item per day. Shows each item's state at the end of each day.

**When to use**: to calculate flow metrics over time (cycle time, historical WIP).

> **RULE**: WorkItemSnapshot **requires** `$apply` with `groupby((DateSK, ...))`. A plain `$filter` won't work — the service returns `400 Bad Request`.

```python
from ado_odata_async.query import Apply

result = await (
    client.query("WorkItemSnapshot")
    .apply(
        Apply()
        .filter(Filter.eq("StateCategory", "InProgress"))
        .groupby("DateSK", "State")
        .aggregate("$count", alias="Count")
    )
    .top(10)
    .get()
)
```

### Comparison table

| Feature | WorkItems | WorkItemRevisions | WorkItemSnapshot |
|---|---|---|---|
| One row represents | Current state of an item | One change to an item | The item's state on a given day |
| Volume | Small (1 per item) | Large (many per item) | Medium (1 per item per day) |
| Used for | "My items" dashboard | Change auditing | Flow metrics |
| Requires `$apply`? | No | No | **Yes** |

---

## State vs StateCategory

In Azure Boards, each work item has a **State** that the team can customize:

- State `Done` (English) / `Concluído` (PT-BR)
- State `In Progress` / `Em Andamento`
- State `To Do` / `A Fazer`

The problem: names change depending on the language and project customization.

The solution: **StateCategory** is a universal classification that works regardless of language:

| StateCategory | Meaning |
|---|---|
| `Proposed` | Item was created but hasn't started yet |
| `InProgress` | Item is being worked on |
| `Completed` | Item is finished |
| `Resolved` | Item is resolved but not yet closed |
| `Removed` | Item was discarded |

**Use StateCategory** in filters instead of State. Example:

```python
# ✅ Correct (works in any project/language)
filter_expr = Filter.eq("StateCategory", "Completed")

# ❌ Fragile (only works if the exact state is 'Done')
filter_expr = Filter.eq("State", "Done")
```

---

## Pagination (`$top` + @odata.nextLink)

Azure DevOps limits how many results a query returns (usually 200 rows). If you need more, you must **paginate**.

The library offers two ways to paginate:

### 1. Automatic pagination with `paginate()`

```python
async for page in client.paginate("WorkItems", top=100):
    for item in page.get("value", []):
        print(item["WorkItemId"], item["Title"])
```

`paginate()` handles:
- Controlling `$skip` / `$top` automatically
- Following the `@odata.nextLink` when present
- Stopping when there's no more data

### 2. Manual pagination with `$skip` and `$top`

```python
page = 0
while True:
    result = await (
        client.query("WorkItems")
        .select("WorkItemId", "Title")
        .skip(page * 100)
        .top(100)
        .get()
    )
    items = result.get("value", [])
    if not items:
        break
    for item in items:
        print(item["WorkItemId"])
    page += 1
```

---

## Flow metrics in 5 minutes

Flow metrics measure how work flows through the team. They're widely used in Kanban and agile methodologies.

### Work item lifecycle

```mermaid
graph LR
    A[Proposed] --> B[InProgress]
    B --> C[Completed]
    style A fill:#e1f5fe
    style B fill:#fff3e0
    style C fill:#e8f5e9
```

### Cycle time

**Definition**: the time an item takes from when it **started being worked on** (`ActivatedDate`) to when it was **finished** (`ClosedDate`).

**What it measures**: the team's delivery speed.

```python
# Conceptual example — see docs/cookbook.md for the full code
from datetime import datetime

# ISO 8601: UTC dates come with "Z" suffix — .replace("Z", "+00:00") makes them Python-readable
activated = datetime.fromisoformat(item["ActivatedDate"].replace("Z", "+00:00"))
closed = datetime.fromisoformat(item["ClosedDate"].replace("Z", "+00:00"))
cycle_time_days = (closed - activated).total_seconds() / 86400
```

### Lead time

**Definition**: the time from when the item was **created** (`CreatedDate`) to when it was **finished** (`ClosedDate`).

**Difference from cycle time**: lead time includes the time the item spent sitting in the queue before someone started working on it.

### Throughput

**Definition**: how many items are finished in a period (usually per week).

**What it measures**: the team's delivery capacity.

```
Weekly throughput:
  Week A: 8 items completed
  Week B: 12 items completed
  Week C: 10 items completed
```

### WIP — Work In Progress

**Definition**: how many items are in progress at a given moment.

**What it measures**: work accumulation. The higher the WIP, the slower the flow.

> WIP (Work In Progress) are the items in `InProgress` state (or equivalent) at a given moment.

### Full diagram

```mermaid
timeline
    title Journey of a work item
    Created : Item created (lead time starts)
    Activated : Someone started working (cycle time starts)
    Closed : Item finished (lead time and cycle time end)
```

---

## Async/await for beginners

If you're used to sequential code (line 1 runs, then line 2, then line 3), `async` might feel strange. Let's simplify.

### The problem

Your code needs to fetch data from the internet. An HTTP request can take 100ms to 5 seconds. In **synchronous** code, the program **stops** and waits:

```
line 1: fetch data (2 seconds of waiting... program frozen...)
line 2: process data
```

During those 2 seconds, the program does nothing else. It's like going to the bank and standing in line unable to do anything while you wait.

### The async/await solution

In **asynchronous** code, while one task waits (network I/O, file, database), other tasks can run:

```
await line 1: starts fetching data  ──┐
                                       │  (2 seconds of waiting,
line 2: processes another calculation  │   but the program continues)
                                       │
line 1: response arrived! continues  ←──┘
```

**The bank analogy**: `await` is like taking a ticket. You hand in the ticket and sit down — you don't stand in line. While your number isn't called, you can read a book, answer emails, etc. When the counter calls your number (`await` completes), you get back up.

### Practical rules

1. **`async def`** before a function means it can use `await` inside.
2. **`await`** before a call means "wait for this operation to finish, but don't block the program — other things can run in the meantime".
3. **`asyncio.run(main())`** is the entry point: "run this async function and wait for it to finish".
4. Everything that uses the network (HTTP, database) MUST be `await`ed — otherwise the program doesn't wait for the response and breaks.

```python
import asyncio


async def my_function() -> None:
    print("Fetching data...")
    result = await some_http_fetch()  # ← doesn't block the program
    print("Data arrived:", result)


asyncio.run(my_function())
```

> **Tip**: if you forget `await`, Python returns an error like `coroutine was never awaited`. It's the most common symptom for beginners with async.

---

## Português (Brasil)

[Português](#english) | **English**

# Conceitos fundamentais

> Público: estagiário de CS (sabe variáveis/loops/funções, nunca viu async/await, OData ou REST).

Este documento explica os conceitos que você precisa entender para usar o `ado-odata-async` com confiança.

---

## O que é OData?

OData (Open Data Protocol) é um padrão que permite consultar dados através de URLs — como se fosse um banco de dados acessível pela web.

**Analogia**: Imagine que o Azure DevOps é um grande arquivo Excel. O OData é como uma "consulta" que você escreve na barra de endereços para buscar só as linhas e colunas que interessam.

Na prática, você monta uma URL com parâmetros especiais:

```
https://analytics.dev.azure.com/minha-org/meu-projeto/_odata/v4.0-preview/WorkItems?$top=10&$select=WorkItemId,Title,State&$filter=WorkItemType eq 'Bug'
```

| Parâmetro | Significado | Exemplo |
|---|---|---|
| `$filter` | Filtra linhas (como WHERE do SQL) | `State eq 'Active'` |
| `$select` | Escolhe colunas (como SELECT) | `WorkItemId,Title` |
| `$top` | Limita resultados | `$top=10` |
| `$orderby` | Ordena | `CreatedDate desc` |
| `$skip` | Pula linhas (para paginação) | `$skip=20` |
| `$expand` | Traz dados relacionados | `$expand=Children` |
| `$apply` | Agrupa e agrega (como GROUP BY) | `groupby((State),aggregate($count as Count))` |

A biblioteca `ado-odata-async` constrói essas URLs para você usando o `QueryBuilder` — você não precisa se preocupar com a sintaxe exata.

---

## Azure DevOps: WorkItems, WorkItemRevisions e WorkItemSnapshot

O Azure Boards expõe três visões diferentes dos dados. Escolher a certa é essencial.

### WorkItems

É o estado **ATUAL** de cada work item. Uma linha por item.

**Quando usar**: para ver o que está aberto agora, quem está assignado, status atual.

```python
result = await (
    client.query("WorkItems")
    .select("WorkItemId", "Title", "State", "AssignedTo")
    .top(10)
    .get()
)
```

### WorkItemRevisions

É o **histórico completo** de todas as mudanças. Cada vez que alguém edita um work item, uma nova revisão é criada.

**Quando usar**: para auditoria, para saber quem mudou o quê e quando.

```python
result = await (
    client.query("WorkItemRevisions")
    .filter(Filter.eq("WorkItemId", 42))
    .select("WorkItemId", "Title", "RevisedDate", "State")
    .get()
)
```

> **ATENÇÃO**: `$expand=Revisions` **não funciona** no Analytics OData (é bloqueado pelo serviço). Sempre use o entity set `WorkItemRevisions` diretamente.

### WorkItemSnapshot

É uma "fotografia" diária: uma linha por work item por dia. Mostra o estado de cada item no final de cada dia.

**Quando usar**: para calcular métricas de fluxo ao longo do tempo (cycle time, WIP histórico).

> **REGRA**: WorkItemSnapshot **requer** `$apply` com `groupby((DateSK, ...))`. Um `$filter` simples não funciona — o serviço retorna `400 Bad Request`.

```python
from ado_odata_async.query import Apply

result = await (
    client.query("WorkItemSnapshot")
    .apply(
        Apply()
        .filter(Filter.eq("StateCategory", "InProgress"))
        .groupby("DateSK", "State")
        .aggregate("$count", alias="Count")
    )
    .top(10)
    .get()
)
```

### Tabela comparativa

| Característica | WorkItems | WorkItemRevisions | WorkItemSnapshot |
|---|---|---|---|
| Uma linha representa | Estado atual de um item | Uma alteração no item | O estado do item em um dia |
| Volume | Pequeno (1 por item) | Grande (muitas por item) | Médio (1 por item por dia) |
| Usado para | Tela "Meus items" | Auditoria de mudanças | Métricas de fluxo |
| Requer `$apply`? | Não | Não | **Sim** |

---

## State vs StateCategory

No Azure Boards, cada work item tem um **State** (estado) que pode ser personalizado pela equipe:

- Estado `Concluído` (PT-BR) / `Done` (inglês)
- Estado `Em Andamento` / `In Progress`
- Estado `A Fazer` / `To Do`

O problema: os nomes mudam conforme o idioma e a customização do projeto.

A solução: **StateCategory** é uma classificação universal que independe do idioma:

| StateCategory | Significado |
|---|---|
| `Proposed` | Item foi criado mas ainda não começou |
| `InProgress` | Item está sendo trabalhado |
| `Completed` | Item foi finalizado |
| `Resolved` | Item foi resolvido mas ainda não fechado |
| `Removed` | Item foi descartado |

**Use StateCategory** nos filtros em vez de State. Exemplo:

```python
# ✅ Correto (funciona em qualquer projeto/idioma)
filter_expr = Filter.eq("StateCategory", "Completed")

# ❌ Frágil (só funciona se o estado exato for 'Concluído')
filter_expr = Filter.eq("State", "Concluído")
```

---

## Paginação (`$top` + @odata.nextLink)

O Azure DevOps limita quantos resultados retorna por consulta (geralmente 200 linhas). Se você precisa de mais, precisa **paginar**.

A biblioteca oferece duas formas de paginar:

### 1. Paginação automática com `paginate()`

```python
async for page in client.paginate("WorkItems", top=100):
    for item in page.get("value", []):
        print(item["WorkItemId"], item["Title"])
```

O `paginate()` cuida de:
- Controlar `$skip` / `$top` automaticamente
- Seguir o link `@odata.nextLink` quando presente
- Parar quando não houver mais dados

### 2. Paginação manual com `$skip` e `$top`

```python
page = 0
while True:
    result = await (
        client.query("WorkItems")
        .select("WorkItemId", "Title")
        .skip(page * 100)
        .top(100)
        .get()
    )
    items = result.get("value", [])
    if not items:
        break
    for item in items:
        print(item["WorkItemId"])
    page += 1
```

---

## Flow metrics em 5 minutos

Flow metrics (métricas de fluxo) medem como o trabalho está fluindo pelo time. São amplamente usadas em Kanban e metodologias ágeis.

### Ciclo de vida de um work item

```mermaid
graph LR
    A[Proposed] --> B[InProgress]
    B --> C[Completed]
    style A fill:#e1f5fe
    style B fill:#fff3e0
    style C fill:#e8f5e9
```

### Cycle time (tempo de ciclo)

**Definição**: o tempo que um item leva desde que **começou a ser trabalhado** (`ActivatedDate`) até ser **finalizado** (`ClosedDate`).

**O que mede**: a velocidade de entrega do time.

```python
# Exemplo conceitual — veja docs/cookbook.md para o código completo
from datetime import datetime

# ISO 8601: datas UTC vêm com sufixo "Z" — .replace("Z", "+00:00") torna-as legíveis pelo Python
activated = datetime.fromisoformat(item["ActivatedDate"].replace("Z", "+00:00"))
closed = datetime.fromisoformat(item["ClosedDate"].replace("Z", "+00:00"))
cycle_time_days = (closed - activated).total_seconds() / 86400
```

### Lead time (tempo de espera total)

**Definição**: o tempo desde que o item foi **criado** (`CreatedDate`) até ser **finalizado** (`ClosedDate`).

**Diferença para cycle time**: lead time inclui o tempo que o item ficou parado na fila antes de alguém começar a trabalhar.

### Throughput (vazão)

**Definição**: quantos items são finalizados em um período (geralmente por semana).

**O que mede**: a capacidade de entrega do time.

```
Throughput semanal:
  Semana A: 8 items concluídos
  Semana B: 12 items concluídos
  Semana C: 10 items concluídos
```

### WIP — Work In Progress (trabalho em andamento)

**Definição**: quantos items estão em andamento em um dado momento.

**O que mede**: o acúmulo de trabalho. Quanto maior o WIP, mais lento o fluxo.

> WIP (Work In Progress) são os items que estão em estado `InProgress` (ou equivalente local) em um dado momento.

### Diagrama completo

```mermaid
timeline
    title Jornada de um work item
    Created : Item foi criado (lead time começa)
    Activated : Alguém começou a trabalhar (cycle time começa)
    Closed : Item foi finalizado (lead time e cycle time terminam)
```

---

## Async/await para quem nunca viu

Se você está acostumado com código sequencial (roda linha 1, depois linha 2, depois linha 3), o `async` pode parecer estranho. Vamos simplificar.

### O problema

Seu código precisa buscar dados na internet. Uma requisição HTTP pode levar de 100ms a 5 segundos. No código **síncrono**, o programa **para** e espera:

```
linha 1: buscar dados (2 segundos de espera... programa travado...)
linha 2: processar dados
```

Durante esses 2 segundos, o programa não faz mais nada. É como ir ao banco e ficar parado na fila sem conseguir fazer mais nada enquanto espera.

### A solução async/await

No código **assíncrono**, enquanto uma tarefa espera (I/O de rede, arquivo, banco), outras tarefas podem rodar:

```
await linha 1: começa a buscar dados  ──┐
                                        │  (2 segundos de espera,
linha 2: processa outro cálculo         │   mas o programa continua)
                                        │
linha 1: resposta chegou! continua   ←──┘
```

**A analogia do banco**: `await` é como pegar uma senha de atendimento. Você entrega a senha e senta — não fica parado em pé na fila. Enquanto seu número não é chamado, você pode ler um livro, responder e-mails, etc. Quando o guichê chama seu número (`await` completa), você volta a andar.

### Regras práticas

1. **`async def`** na frente de uma função significa que ela pode usar `await` dentro.
2. **`await`** na frente de uma chamada significa "espere essa operação terminar, mas não trave o programa — outras coisas podem rodar enquanto isso".
3. **`asyncio.run(main())`** é o ponto de entrada: "rode essa função assíncrona e espere ela terminar".
4. Tudo que usa rede (HTTP, banco) DEVE ser `await` — senão o programa não espera a resposta e quebra.

```python
import asyncio


async def minha_funcao() -> None:
    print("Vou buscar dados...")
    resultado = await alguma_busca_http()  # ← não trava o programa
    print("Dados chegaram:", resultado)


asyncio.run(minha_funcao())
```

> **Dica**: se você esquecer o `await`, o Python retorna um erro como `coroutine was never awaited`. É o sintoma mais comum de quem está começando com async.
