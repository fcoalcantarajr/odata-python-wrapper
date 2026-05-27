# Glossário

> Lista alfabética de termos técnicos usados na biblioteca e na documentação.

---

## `$apply`

**Definição**: Parâmetro OData usado para agrupar e agregar dados (como GROUP BY do SQL). É **obrigatório** para consultar `WorkItemSnapshot`.

**Exemplo**: `$apply=groupby((DateSK,State))/aggregate(WorkItemId with countdistinct as WorkItemId)`

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

**Definição**: Token de segurança usado para autenticar no Azure DevOps. Substitui senha e permite limitar escopos (permissões). O username deve ser vazio (HR-8, gotcha 1).

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

**Definição**: Classificação universal do estado de um work item, que não depende do idioma ou personalização. Valores: `Proposed`, `InProgress`, `Completed`, `Removed`.

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
