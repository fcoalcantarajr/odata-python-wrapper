# Solução de problemas

> Cada entrada começa com o **sintoma** (o que você vê na tela). A causa vem depois.

---

## 401 Unauthorized

**O que você vê**:
```
ado_odata_async.exceptions.AuthenticationError: 401 Unauthorized
```

**Causa mais comum**: seu PAT (Personal Access Token) expirou ou não tem os escopos corretos.

**O que fazer**:
1. Acesse `https://dev.azure.com/{sua-org}/_usersSettings/tokens`
2. Localize o token que está usando
3. Se estiver expirado, crie um novo (expiração de 30 dias)
4. Se estiver ativo, verifique os escopos: precisa ter **Work Items (Read)** e **Analytics (Read)**
5. Atualize o `.env` com o novo token

**Como prevenir**:
- Defina a expiração para 30 ou 90 dias e crie um lembrete na agenda
- Use a biblioteca com `try/except AuthenticationError` para capturar o erro sem quebrar o script (veja [Receita 7 no Cookbook](cookbook.md#7-tratar-erros-de-autenticação-e-rede))

---

## HTTP 203 + página de login HTML no response

**O que você vê**:
```
ado_odata_async.exceptions.AuthenticationError: HTTP 203 Non-Authoritative Information
```
E o corpo da resposta é HTML (página de login da Microsoft).

**Causa**: O Azure DevOps retorna HTTP 203 com conteúdo HTML quando o PAT é inválido **ou** a URL da organização está errada. Pode acontecer quando:
- O PAT foi revogado
- A organização não existe ou o nome está incorreto
- O SSO/MFA da sua empresa está bloqueando tokens não interativos

**O que fazer**:
1. Verifique se o nome da organização no `.env` está correto
2. Crie um novo PAT
3. Se o problema persistir, sua empresa pode ter políticas de segurança que bloqueiam PATs — fale com o tech lead

**Como prevenir**: Teste o PAT manualmente antes de rodar o script:
```bash
curl -u :$ADO_PAT -H "Content-Type: application/json" \
  "https://analytics.dev.azure.com/$ADO_ORG/$ADO_PROJECT/_odata/v4.0-preview/WorkItems?\$top=1"
```
Se o curl retornar JSON, o PAT funciona. Se retornar HTML, o PAT é inválido.

---

## 400 Bad Request no WorkItemSnapshot

**O que você vê**:
```
ado_odata_async.exceptions.BadRequestError: 400 Bad Request
```
(quando consulta `WorkItemSnapshot` sem `$apply`)

**Causa**: O entity set `WorkItemSnapshot` **requer** `$apply` com `groupby`. Um `$filter` simples não é aceito pelo serviço (HR-13, gotcha 4).

**O que fazer**: Use `$apply` com `groupby((DateSK, ...))`:

```python
# ❌ ERRADO: filtro simples não funciona
client.query("WorkItemSnapshot").filter(Filter.eq("State", "Active")).get()

# ✅ CORRETO: use $apply com groupby
from ado_odata_async.query import Apply

    client.query("WorkItemSnapshot").apply(
        Apply()
        .filter(Filter.eq("State", "Active"))
        .groupby("DateSK", "State")
        .aggregate("$count", alias="Count")
    ).top(10).get()
```

**Como prevenir**: A própria biblioteca valida isso! Se você esquecer o `groupby`, o `QueryBuilder` lança um `ValueError` antes de fazer a requisição.

---

## 400 Bad Request com aggregate — "as alias"

**O que você vê**:
```
ado_odata_async.exceptions.BadRequestError: 400 Bad Request
```
(quando sua expressão `$apply` tem `aggregate`)

**Causa**: O Azure DevOps Analytics exige que cada aggregate tenha um alias com `as <nome>`. Exemplo:
```
# ✅ Correto (a biblioteca gera automaticamente)
aggregate(Effort with sum as Effort)

# ❌ Errado (o serviço rejeita)
aggregate(Effort with sum)
```

**O que fazer**: Se você está montando a query manualmente (sem o `Apply` builder), inclua o `as <alias>`. Se está usando o `Apply` builder, ele já gera o alias automaticamente — nenhuma ação necessária.

---

## 400 Bad Request com aggregate — ordem dos argumentos

**O que você vê**:
```
ado_odata_async.exceptions.BadRequestError: 400 Bad Request
```
(quando usa `aggregate` com os argumentos trocados)

**Causa**: O método `aggregate(field, method)` espera o **campo/propriedade** primeiro e o **método de agregação** em segundo. A ordem canônica do OData é `$apply=aggregate(field with method as field)`. Trocar os argumentos gera uma expressão inválida, como `aggregate(Count with WorkItemId as Count)` em vez de `aggregate(WorkItemId with sum as WorkItemId)`.

Além disso, o nome do método deve estar em **minúsculas**. Os métodos válidos no Azure DevOps Analytics v4.0-preview são:
- `sum` — soma dos valores
- `min` — valor mínimo
- `max` — valor máximo
- `average` — média aritmética

**O que fazer**: Verifique a ordem da chamada:
```python
# ❌ ERRADO: método na posição do campo, campo na posição do método
Apply().groupby("State").aggregate("Count", "WorkItemId")   # "Count" vira método — inválido
Apply().groupby("State").aggregate("Sum", "Effort")

# ✅ CORRETO: campo primeiro, método em segundo (minúsculas)
Apply().groupby("State").aggregate("WorkItemId", "sum")
Apply().groupby("State").aggregate("Effort", "sum")
```

**Como prevenir**: Sempre escreva `aggregate("<campo>", "<método>")` — o campo é o dado que você quer agregar (ex.: `Effort`, `WorkItemId`, `StoryPoints`), o método é a operação (`sum`, `min`, `max`, `average`). Para contagem de linhas, use `aggregate("$count", alias="Nome")`.

---

## ValidationError do Pydantic

**O que você vê**:
```
pydantic.ValidationError: 1 validation error for WorkItem
  Field required [type=missing, input_value={...}, input_type=dict]
```

**Causa**: O Azure DevOps retornou um campo que o modelo Pydantic não espera, ou deixou de retornar um campo obrigatório. Isso pode acontecer quando a Microsoft adiciona novos campos ao esquema OData.

**O que fazer**:
1. Anote quais campos estão causando o erro (a mensagem mostra o JSON recebido)
2. Crie uma [issue no GitHub](https://github.com/ohmyopencode/odata-python-wrapper/issues) com o JSON completo
3. Como workaround temporário, use `client.get()` em vez do modelo tipado (retorna `dict`)

```python
# Workaround: use get() em vez de get_workitem()
dados = await client.get("WorkItems", **{"$filter": "WorkItemId eq 42"})
print(dados["value"][0]["Title"])  # dicionário comum, sem validação Pydantic
```

---

## ModuleNotFoundError: aioresponses

**O que você vê**:
```
ModuleNotFoundError: No module named 'aioresponses'
```
(ou similar com `pytest`, `hypothesis`, etc.)

**Causa**: Você rodou `uv sync` sem a flag `--all-groups`, então as dependências de desenvolvimento não foram instaladas.

**O que fazer**:
```bash
uv sync --all-groups
```

**Como prevenir**: Sempre use `--all-groups` ao clonar o projeto pela primeira vez.

---

## URL too long (HTTP 414)

**O que você vê**:
```
aiohttp.ClientResponseError: 414 URI Too Long
```

**Causa**: A URL da requisição excedeu o limite do servidor (geralmente 8192 caracteres, mas o Azure DevOps Analytics é mais restritivo).

**O que fazer**: Nada — a biblioteca já lida com isso automaticamente. Quando a URL ultrapassa 3000 caracteres (padrão), o `AdoODataClient` converte a requisição para `POST $batch` com `multipart/mixed`. Você pode ajustar o limite:

```python
# Threshold menor: URLs > 2000 chars viram POST $batch
async with AdoODataClient(org=org, project=project, pat=pat, batch_threshold=2000) as client:
    ...
```

---

## NameError em testes

**O que você vê**:
```
NameError: name 'asyncio' is not defined
```
(ou erro de marker ao rodar `pytest`)

**Causa**: O arquivo `pyproject.toml` já tem o marker `asyncio` configurado, mas se você estiver rodando fora do projeto configurado, o pytest pode não reconhecer.

**O que fazer**:
```bash
uv run pytest
```
(Não use `pytest` diretamente — sempre use `uv run pytest` dentro do projeto.)

---

## VS403483 — groupby grouping expression must evaluate to a property access value

**O que você vê**:
```
VS403483: $apply/groupby grouping expression 'WorkItemId' must evaluate to a property access value.
```
(HTTP 400 Bad Request)

**Causa**: Duas causas simultâneas, ambas corrigidas na F12:

1. **`countdistinct` é bloqueado pelo ADO Analytics.** A função `countdistinct` existe no OData, mas o Azure DevOps Analytics **não aceita**. A Microsoft afirma que suporte futuro está planejado, mas hoje o uso retorna erro.
   - [Documentação: "DON'T use countdistinct aggregation"](https://learn.microsoft.com/en-us/azure/devops/report/extend-analytics/odata-query-guidelines?view=azure-devops)

2. **`aggregate` deve ser ANINHADO dentro de `groupby`, não encadeado com `/`.** A sintaxe correta do OData é:
   ```
   groupby((State, DateValue), aggregate($count as Count, StoryPoints with sum as TotalStoryPoints))
   ```
   A forma incorreta `groupby((...))/aggregate(...)` gera o erro VS403483 porque, após o `groupby` standalone, apenas os campos de agrupamento estão no escopo — o campo do aggregate (ex.: `WorkItemId`) não é reconhecido.
   - [Documentação: OData supported features](https://learn.microsoft.com/en-us/azure/devops/report/extend-analytics/odata-supported-features?view=azure-devops)

**Solução** (a biblioteca já implementa desde a versão com F12):

```python
# ✅ CORRETO: aggregate dentro de groupby, usando $count em vez de countdistinct
from ado_odata_async.query import Apply, Filter

Apply()
    .filter(Filter.eq("StateCategory", "Completed"))
    .groupby("DateSK", "State")
    .aggregate("$count", alias="Count")
    .build()
# → "$apply=filter(StateCategory eq 'Completed')/groupby((DateSK,State),aggregate($count as Count))"
```

**Como prevenir**:
- Nunca use `countdistinct` como método de agregação — use `$count` com `alias` para contagem de linhas.
- O aggregate é automaticamente aninhado dentro do groupby quando são consecutivos na chamada fluente.
- Se precisar de contagem distinta, use `$count` dentro de `groupby` com os campos de desejados no agrupamento.
