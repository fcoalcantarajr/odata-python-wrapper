**English** | [Português](#português-brasil)

# Glossary

> Alphabetical list of technical terms used in the library and documentation.

---

## `$apply`

**Definition**: OData parameter used to group and aggregate data (like SQL GROUP BY). It is **required** when querying `WorkItemSnapshot`.

**Example**: `$apply=filter(StateCategory eq 'Completed')/groupby((DateSK,State),aggregate($count as Count))`

**See also**: [WorkItemSnapshot](#workitemsnapshot), [Cookbook recipe 8](cookbook.md#8-use-the-apply-dsl-with-aggregate)

---

## `$filter`

**Definition**: OData parameter for filtering rows (like SQL WHERE). Used with the library's [Filter](#filter) class.

**Example**: `$filter=State eq 'Active'`

**See also**: [Filter](#filter), [Concepts: OData](concepts.md#what-is-odata)

---

## `$orderby`

**Definition**: OData parameter for sorting results.

**Example**: `$orderby=CreatedDate desc`

**See also**: [Concepts: OData](concepts.md#what-is-odata)

---

## `$select`

**Definition**: OData parameter for choosing which columns (properties) to fetch. Fewer columns = faster response.

**Example**: `$select=WorkItemId,Title,State`

**See also**: [Concepts: OData](concepts.md#what-is-odata)

---

## `$top`

**Definition**: OData parameter for limiting the number of results returned.

**Example**: `$top=10` returns at most 10 rows.

**See also**: [Concepts: Pagination](concepts.md#pagination-top--odatanextlink)

---

## Analytics

**Definition**: The Azure DevOps service that exposes work tracking data through the OData (Open Data Protocol) API. It's the official source for flow metrics and reports.

**Example**: The Analytics base URL is `https://analytics.dev.azure.com/{org}/{project}/_odata/v4.0-preview/`

**See also**: [OData](#odata)

---

## async/await

**Definition**: Python features for asynchronous programming. `await` means "wait for this operation to finish, but don't block the program — other tasks can run in the meantime". `async` marks a function as asynchronous.

**Example**:
```python
async def fetch() -> None:
    result = await client.get("WorkItems")
    print(result)
```

**See also**: [Concepts: Async/await](concepts.md#asyncawait-for-beginners)

---

## Azure Boards

**Definition**: The work management tool in Azure DevOps, used to track tasks, bugs, user stories, and other types of work item.

**Example**: Where you create cards ("work items") to organize the team's work.

**See also**: [WorkItem](#workitem)

---

## cycle time

**Definition**: The time a work item takes from when it **started being worked on** (ActivatedDate) to when it was **finished** (ClosedDate). The most important flow metric.

**Example**: If a bug was activated on 05/01 and closed on 05/05, the cycle time is 4 days.

**See also**: [lead time](#lead-time), [throughput](#throughput), [Concepts: Flow metrics](concepts.md#flow-metrics-in-5-minutes)

---

## Filter

**Definition**: Library class that builds OData filter expressions. Supports `eq`, `ne`, `gt`, `ge`, `lt`, `le`, `and_`, `or_`, `not_`, `contains`.

**Example**: `Filter.and_(Filter.eq("State", "Active"), Filter.eq("WorkItemType", "Bug"))`

**See also**: [`$filter`](#filter-1)

---

## lead time

**Definition**: The time from when the work item was **created** (CreatedDate) to when it was **finished** (ClosedDate). Includes the time the item spent in the queue before someone started working on it.

**Example**: An item created on 05/01 and closed on 05/10 has a lead time of 9 days. If the cycle time is 4 days, it means the item sat in the queue for 5 days.

**See also**: [cycle time](#cycle-time), [Concepts: Flow metrics](concepts.md#flow-metrics-in-5-minutes)

---

## OData (Open Data Protocol)

**Definition**: A standard protocol for querying data through URLs, with parameters like `$filter`, `$select`, `$top`. Works like a "database API" over HTTP.

**Example**: `https://.../_odata/v4.0-preview/WorkItems?$top=5`

**See also**: [Concepts: OData](concepts.md#what-is-odata)

---

## pagination

**Definition**: A technique for fetching large datasets in batches (pages). The library provides `client.paginate()` which controls `$skip`/`$top` and `@odata.nextLink` automatically.

**Example**:
```python
async for page in client.paginate("WorkItems", top=100):
    ...
```

**See also**: [Concepts: Pagination](concepts.md#pagination-top--odatanextlink)

---

## PAT (Personal Access Token)

**Definition**: A security token used to authenticate with Azure DevOps. Replaces passwords and allows limiting scopes (permissions). The username must be empty.

**Example**: A PAT looks like a random string: `6bRG37jI...`

> ⚠️ **Security**: Use minimum scopes (read-only), short expiration (30 days), never commit to git.

**See also**: [Getting started: Creating your PAT](getting-started.md#creating-your-pat-personal-access-token)

---

## pydantic

**Definition**: A Python library for data validation using typed models. The library uses `pydantic` to ensure that data returned by Azure DevOps has the expected format.

**Example**: The library's `WorkItem` model is a Pydantic class that automatically validates the fields in the returned JSON.

**See also**: [WorkItem](#workitem)

---

## State

**Definition**: The current state of a work item, defined by the team. Names vary depending on the language and project customization (e.g., "Done", "Concluído", "Feito").

**Example**: `State eq 'Done'` (English) vs `State eq 'Concluído'` (PT-BR).

**See also**: [StateCategory](#statecategory)

---

## StateCategory

**Definition**: A universal classification of a work item's state that doesn't depend on language or customization. Values: `Proposed`, `InProgress`, `Completed`, `Resolved`, `Removed`.

**Example**: `StateCategory eq 'Completed'` works in any project, regardless of whether the localized state is "Done" or "Concluído".

**See also**: [State](#state), [Concepts: State vs StateCategory](concepts.md#state-vs-statecategory)

---

## throughput

**Definition**: The number of work items finished in a period (usually per week). Measures the team's delivery capacity.

**Example**: "We closed 12 items this week" — that's the weekly throughput.

**See also**: [cycle time](#cycle-time), [Concepts: Flow metrics](concepts.md#flow-metrics-in-5-minutes)

---

## WIP (Work In Progress)

**Definition**: The number of work items that are in progress at a given moment. The higher the WIP, the slower the flow.

**Example**: If on 05/15 there are 8 items in "In Progress" state, the WIP that day is 8.

**See also**: [cycle time](#cycle-time), [lead time](#lead-time)

---

## work item

**Definition**: A record in Azure Boards that represents a unit of work — can be a task, a bug, a user story, etc.

**Example**: "Create login screen" is a work item of type "Task".

**See also**: [WorkItem](#workitem), [Azure Boards](#azure-boards)

---

## WorkItem

**Definition**: The library's Pydantic model representing the current state of a work item in Azure Boards. Contains fields like `WorkItemId`, `Title`, `State`, `WorkItemType`.

**Example**: `wi = await client.get_workitem(42)` returns a `WorkItem` instance.

**See also**: [WorkItemRevisions](#workitemrevisions), [WorkItemSnapshot](#workitemsnapshot)

---

## WorkItemRevisions

**Definition**: Entity set and Pydantic model representing the complete history of changes to a work item. Each revision is one row.

**Example**: `client.query("WorkItemRevisions").filter(Filter.eq("WorkItemId", 42)).get()`

**See also**: [WorkItem](#workitem), [Concepts: WorkItemRevisions](concepts.md#workitemrevisions)

---

## WorkItemSnapshot

**Definition**: Entity set that stores a daily "snapshot" of each work item. One row per item per day. Requires `$apply` with `groupby((DateSK, ...))`.

**Example**: Used to calculate historical WIP or cycle time over time.

**See also**: [WorkItem](#workitem), [`$apply`](#apply), [Concepts: WorkItemSnapshot](concepts.md#workitemsnapshot)

---

## Português (Brasil)

[Português](#english) | **English**

# Glossário

> Lista alfabética de termos técnicos usados na biblioteca e na documentação.

---

## `$apply`

**Definição**: Parâmetro OData usado para agrupar e agregar dados (como GROUP BY do SQL). É **obrigatório** para consultar `WorkItemSnapshot`.

**Exemplo**: `$apply=filter(StateCategory eq 'Completed')/groupby((DateSK,State),aggregate($count as Count))`

**Veja também**: [WorkItemSnapshot](#workitemsnapshot), [Cookbook receita 8](cookbook.md#8-usar-apply-dsl-com-aggregate)

---

## `$filter`

**Definição**: Parâmetro OData para filtrar linhas (como WHERE do SQL). Usado com a classe [Filter](#filter) da biblioteca.

**Exemplo**: `$filter=State eq 'Active'`

**Veja também**: [Filter](#filter), [Conceitos: OData](concepts.md#o-que-é-odata)

---

## `$orderby`

**Definição**: Parâmetro OData para ordenar resultados.

**Exemplo**: `$orderby=CreatedDate desc`

**Veja também**: [Conceitos: OData](concepts.md#o-que-é-odata)

---

## `$select`

**Definição**: Parâmetro OData para escolher quais colunas (propriedades) trazer. Menos colunas = resposta mais rápida.

**Exemplo**: `$select=WorkItemId,Title,State`

**Veja também**: [Conceitos: OData](concepts.md#o-que-é-odata)

---

## `$top`

**Definição**: Parâmetro OData para limitar o número de resultados retornados.

**Exemplo**: `$top=10` retorna no máximo 10 linhas.

**Veja também**: [Conceitos: Paginação](concepts.md#paginação-top--odatanextlink)

---

## Analytics

**Definição**: Serviço do Azure DevOps que expõe dados de work tracking através da API OData (Open Data Protocol). É a fonte oficial para métricas de fluxo e relatórios.

**Exemplo**: A URL base do Analytics é `https://analytics.dev.azure.com/{org}/{project}/_odata/v4.0-preview/`

**Veja também**: [OData](#odata)

---

## async/await

**Definição**: Recursos do Python para programação assíncrona. `await` diz "espere esta operação terminar, mas não trave o programa — outras tarefas podem executar enquanto isso". `async` marca uma função como assíncrona.

**Exemplo**:
```python
async def buscar() -> None:
    resultado = await client.get("WorkItems")
    print(resultado)
```

**Veja também**: [Conceitos: Async/await](concepts.md#asyncawait-para-quem-nunca-viu)

---

## Azure Boards

**Definição**: Ferramenta de gerenciamento de trabalho do Azure DevOps, usada para acompanhar tarefas, bugs, histórias de usuário e outros tipos de work item.

**Exemplo**: Onde você cria cards ("work items") para organizar o trabalho do time.

**Veja também**: [WorkItem](#workitem)

---

## cycle time (tempo de ciclo)

**Definição**: Tempo que um work item leva desde que **começou a ser trabalhado** (ActivatedDate) até ser **finalizado** (ClosedDate). A métrica mais importante de fluxo.

**Exemplo**: Se um bug foi ativado em 01/05 e fechado em 05/05, o cycle time é 4 dias.

**Veja também**: [lead time](#lead-time-time-de-espera-total), [throughput](#throughput-vazo), [Conceitos: Flow metrics](concepts.md#flow-metrics-em-5-minutos)

---

## Filter

**Definição**: Classe da biblioteca que constrói expressões de filtro OData. Suporta `eq`, `ne`, `gt`, `ge`, `lt`, `le`, `and_`, `or_`, `not_`, `contains`.

**Exemplo**: `Filter.and_(Filter.eq("State", "Active"), Filter.eq("WorkItemType", "Bug"))`

**Veja também**: [`$filter`](#filter-1)

---

## lead time (tempo de espera total)

**Definição**: Tempo desde que o work item foi **criado** (CreatedDate) até ser **finalizado** (ClosedDate). Inclui o tempo em fila antes de alguém começar a trabalhar.

**Exemplo**: Um item criado em 01/05 e fechado em 10/05 tem lead time de 9 dias. Se o cycle time é 4 dias, significa que ficou 5 dias parado na fila.

**Veja também**: [cycle time](#cycle-time-tempo-de-ciclo), [Conceitos: Flow metrics](concepts.md#flow-metrics-em-5-minutos)

---

## OData (Open Data Protocol)

**Definição**: Protocolo padrão que permite consultar dados através de URLs, com parâmetros como `$filter`, `$select`, `$top`. Funciona como uma "API de banco de dados" via HTTP.

**Exemplo**: `https://.../_odata/v4.0-preview/WorkItems?$top=5`

**Veja também**: [Conceitos: OData](concepts.md#o-que-é-odata)

---

## paginação

**Definição**: Técnica para buscar grandes volumes de dados em lotes (páginas). A biblioteca oferece `client.paginate()` que controla `$skip`/`$top` e `@odata.nextLink` automaticamente.

**Exemplo**:
```python
async for page in client.paginate("WorkItems", top=100):
    ...
```

**Veja também**: [Conceitos: Paginação](concepts.md#paginação-top--odatanextlink)

---

## PAT (Personal Access Token)

**Definição**: Token de segurança usado para autenticar no Azure DevOps. Substitui senha e permite limitar escopos (permissões). O username deve ser vazio.

**Exemplo**: Um PAT começa com aparência de string aleatória: `6bRG37jI...`

> ⚠️ **Segurança**: PAT com escopo mínimo (só leitura), expiração curta (30 dias), nunca versionado no git.

**Veja também**: [Guia de início rápido: Criando seu PAT](getting-started.md#criando-seu-pat-personal-access-token)

---

## pydantic

**Definição**: Biblioteca Python para validação de dados via modelos com tipos. A biblioteca usa `pydantic` para garantir que os dados retornados pelo Azure DevOps tenham o formato esperado.

**Exemplo**: O modelo `WorkItem` da biblioteca é uma classe Pydantic que valida automaticamente os campos do JSON retornado.

**Veja também**: [WorkItem](#workitem)

---

## State

**Definição**: O estado atual de um work item, definido pelo time. Os nomes variam conforme o idioma e a personalização do projeto (ex.: "Concluído", "Done", "Feito").

**Exemplo**: `State eq 'Concluído'` (PT-BR) vs `State eq 'Done'` (inglês).

**Veja também**: [StateCategory](#statecategory)

---

## StateCategory

**Definição**: Classificação universal do estado de um work item, que não depende do idioma ou personalização. Valores: `Proposed`, `InProgress`, `Completed`, `Resolved`, `Removed`.

**Exemplo**: `StateCategory eq 'Completed'` funciona em qualquer projeto, independente de o estado localizado ser "Concluído" ou "Done".

**Veja também**: [State](#state), [Conceitos: State vs StateCategory](concepts.md#state-vs-statecategory)

---

## throughput (vazão)

**Definição**: Quantidade de work items finalizados em um período (geralmente por semana). Mede a capacidade de entrega do time.

**Exemplo**: "Fechamos 12 items esta semana" — esse é o throughput semanal.

**Veja também**: [cycle time](#cycle-time-tempo-de-ciclo), [Conceitos: Flow metrics](concepts.md#flow-metrics-em-5-minutos)

---

## WIP (Work In Progress)

**Definição**: Quantidade de work items que estão em andamento em um dado momento. Quanto maior o WIP, mais lento o fluxo.

**Exemplo**: Se em 15/05 existem 8 items em estado "In Progress", o WIP naquele dia é 8.

**Veja também**: [cycle time](#cycle-time-tempo-de-ciclo), [lead time](#lead-time-time-de-espera-total)

---

## work item

**Definição**: Um registro no Azure Boards que representa uma unidade de trabalho — pode ser uma tarefa, um bug, uma história de usuário, etc.

**Exemplo**: "Criar tela de login" é um work item do tipo "Tarefa".

**Veja também**: [WorkItem](#workitem), [Azure Boards](#azure-boards)

---

## WorkItem

**Definição**: Modelo Pydantic da biblioteca que representa o estado atual de um work item no Azure Boards. Contém campos como `WorkItemId`, `Title`, `State`, `WorkItemType`.

**Exemplo**: `wi = await client.get_workitem(42)` retorna uma instância de `WorkItem`.

**Veja também**: [WorkItemRevisions](#workitemrevisions), [WorkItemSnapshot](#workitemsnapshot)

---

## WorkItemRevisions

**Definição**: Entity set e modelo Pydantic que representa o histórico completo de alterações de um work item. Cada revisão é uma linha.

**Exemplo**: `client.query("WorkItemRevisions").filter(Filter.eq("WorkItemId", 42)).get()`

**Veja também**: [WorkItem](#workitem), [Conceitos: WorkItemRevisions](concepts.md#workitemrevisions)

---

## WorkItemSnapshot

**Definição**: Entity set que armazena uma "fotografia" diária de cada work item. Uma linha por item por dia. Requer `$apply` com `groupby((DateSK, ...))`.

**Exemplo**: Usado para calcular WIP histórico ou cycle time ao longo do tempo.

**Veja também**: [WorkItem](#workitem), [`$apply`](#apply), [Conceitos: WorkItemSnapshot](concepts.md#workitemsnapshot)
