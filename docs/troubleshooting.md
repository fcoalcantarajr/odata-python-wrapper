**English** | [Português](#português-brasil)

# Troubleshooting

> Each entry starts with the **symptom** (what you see on screen). The cause comes after.

---

## 401 Unauthorized

**What you see**:
```
ado_odata_async.exceptions.AuthenticationError: 401 Unauthorized
```

**Most common cause**: your PAT (Personal Access Token) expired or has the wrong scopes.

**What to do**:
1. Go to `https://dev.azure.com/{your-org}/_usersSettings/tokens`
2. Find the token you're using
3. If it's expired, create a new one (30-day expiration)
4. If it's active, check the scopes: it needs **Work Items (Read)** and **Analytics (Read)**
5. Update `.env` with the new token

**How to prevent**:
- Set expiration to 30 or 90 days and create a calendar reminder
- Use `try/except AuthenticationError` in your script to catch the error without crashing (see [Recipe 7 in the Cookbook](cookbook.md#7-handle-authentication-and-network-errors))

---

## HTTP 203 + HTML login page in response

**What you see**:
```
ado_odata_async.exceptions.AuthenticationError: HTTP 203 Non-Authoritative Information
```
And the response body is HTML (Microsoft login page).

**Cause**: Azure DevOps returns HTTP 203 with HTML content when the PAT is invalid **or** the organization URL is wrong. This can happen when:
- The PAT was revoked
- The organization doesn't exist or the name is incorrect
- Your company's SSO/MFA is blocking non-interactive tokens

**What to do**:
1. Check that the organization name in `.env` is correct
2. Create a new PAT
3. If the problem persists, your company may have security policies blocking PATs — talk to your tech lead

**How to prevent**: Test the PAT manually before running the script:
```bash
curl -u :$ADO_PAT -H "Content-Type: application/json" \
  "https://analytics.dev.azure.com/$ADO_ORG/$ADO_PROJECT/_odata/v4.0-preview/WorkItems?\$top=1"
```
If curl returns JSON, the PAT works. If it returns HTML, the PAT is invalid.

---

## 400 Bad Request on WorkItemSnapshot

**What you see**:
```
ado_odata_async.exceptions.BadRequestError: 400 Bad Request
```
(when querying `WorkItemSnapshot` without `$apply`)

**Cause**: The `WorkItemSnapshot` entity set **requires** `$apply` with `groupby`. A plain `$filter` is not accepted by the service.

**What to do**: Use `$apply` with `groupby((DateSK, ...))`:

```python
# ❌ WRONG: plain filter doesn't work
client.query("WorkItemSnapshot").filter(Filter.eq("State", "Active")).get()

# ✅ CORRECT: use $apply with groupby
from ado_odata_async.query import Apply

    client.query("WorkItemSnapshot").apply(
        Apply()
        .filter(Filter.eq("State", "Active"))
        .groupby("DateSK", "State")
        .aggregate("$count", alias="Count")
    ).top(10).get()
```

**How to prevent**: The library validates this automatically! If you forget `groupby`, the `QueryBuilder` raises a `ValueError` before making the request.

---

## 400 Bad Request with aggregate — "as alias"

**What you see**:
```
ado_odata_async.exceptions.BadRequestError: 400 Bad Request
```
(when your `$apply` expression has `aggregate`)

**Cause**: Azure DevOps Analytics requires each aggregate to have an alias with `as <name>`. Example:
```
# ✅ Correct (library generates automatically)
aggregate(Effort with sum as Effort)

# ❌ Wrong (service rejects)
aggregate(Effort with sum)
```

**What to do**: If you're building the query manually (without the `Apply` builder), include `as <alias>`. If you're using the `Apply` builder, it already generates the alias automatically — no action needed.

---

## 400 Bad Request with aggregate — wrong argument order

**What you see**:
```
ado_odata_async.exceptions.BadRequestError: 400 Bad Request
```
(when using `aggregate` with arguments swapped)

**Cause**: The `aggregate(field, method)` method expects the **field/property** first and the **aggregation method** second. The canonical OData order is `$apply=aggregate(field with method as field)`. Swapping arguments generates an invalid expression, like `aggregate(Count with WorkItemId as Count)` instead of `aggregate(WorkItemId with sum as WorkItemId)`.

Additionally, the method name must be **lowercase**. Valid methods in Azure DevOps Analytics v4.0-preview are:
- `sum` — sum of values
- `min` — minimum value
- `max` — maximum value
- `average` — arithmetic mean

**What to do**: Check the call order:
```python
# ❌ WRONG: method in field position, field in method position
Apply().groupby("State").aggregate("Count", "WorkItemId")   # "Count" becomes method — invalid
Apply().groupby("State").aggregate("Sum", "Effort")

# ✅ CORRECT: field first, method second (lowercase)
Apply().groupby("State").aggregate("WorkItemId", "sum")
Apply().groupby("State").aggregate("Effort", "sum")
```

**How to prevent**: Always write `aggregate("<field>", "<method>")` — the field is the data you want to aggregate (e.g., `Effort`, `WorkItemId`, `StoryPoints`), the method is the operation (`sum`, `min`, `max`, `average`). For row counting, use `aggregate("$count", alias="Name")`.

---

## Pydantic ValidationError

**What you see**:
```
pydantic.ValidationError: 1 validation error for WorkItem
  Field required [type=missing, input_value={...}, input_type=dict]
```

**Cause**: Azure DevOps returned a field that the Pydantic model doesn't expect, or stopped returning a required field. This can happen when Microsoft adds new fields to the OData schema.

**What to do**:
1. Note which fields are causing the error (the message shows the received JSON)
2. [Open an issue on GitHub](https://github.com/ohmyopencode/odata-python-wrapper/issues) with the full JSON
3. As a temporary workaround, use `client.get()` instead of the typed model (returns `dict`)

```python
# Workaround: use get() instead of get_workitem()
data = await client.get("WorkItems", **{"$filter": "WorkItemId eq 42"})
print(data["value"][0]["Title"])  # plain dict, no Pydantic validation
```

---

## ModuleNotFoundError: aioresponses

**What you see**:
```
ModuleNotFoundError: No module named 'aioresponses'
```
(or similar with `pytest`, `hypothesis`, etc.)

**Cause**: You ran `uv sync` without the `--all-groups` flag, so development dependencies weren't installed.

**What to do**:
```bash
uv sync --all-groups
```

**How to prevent**: Always use `--all-groups` when cloning the project for the first time.

---

## URL too long (HTTP 414)

**What you see**:
```
aiohttp.ClientResponseError: 414 URI Too Long
```

**Cause**: The request URL exceeded the server limit (usually 8192 characters, but Azure DevOps Analytics is stricter).

**What to do**: Nothing — the library handles this automatically. When the URL exceeds 3000 characters (default), `AdoODataClient` converts the request to `POST $batch` with `multipart/mixed`. You can adjust the threshold:

```python
# Lower threshold: URLs > 2000 chars become POST $batch
async with AdoODataClient(org=org, project=project, pat=pat, batch_threshold=2000) as client:
    ...
```

---

## NameError in tests

**What you see**:
```
NameError: name 'asyncio' is not defined
```
(or marker error when running `pytest`)

**Cause**: The `pyproject.toml` already has the `asyncio` marker configured, but if you're running outside the configured project, pytest may not recognize it.

**What to do**:
```bash
uv run pytest
```
(Don't use `pytest` directly — always use `uv run pytest` inside the project.)

---

## VS403483 — groupby grouping expression must evaluate to a property access value

**What you see**:
```
VS403483: $apply/groupby grouping expression 'WorkItemId' must evaluate to a property access value.
```
(HTTP 400 Bad Request)

**Cause**: Two simultaneous causes, both fixed in F12:

1. **`countdistinct` is blocked by ADO Analytics.** The `countdistinct` function exists in OData, but Azure DevOps Analytics **does not accept it**. Microsoft states future support is planned, but currently it returns an error.
   - [Documentation: "DON'T use countdistinct aggregation"](https://learn.microsoft.com/en-us/azure/devops/report/extend-analytics/odata-query-guidelines?view=azure-devops)

2. **`aggregate` must be NESTED inside `groupby`, not chained with `/`.** The correct OData syntax is:
   ```
   groupby((State, DateValue), aggregate($count as Count, StoryPoints with sum as TotalStoryPoints))
   ```
   The incorrect `groupby((...))/aggregate(...)` generates the VS403483 error because, after a standalone `groupby`, only the grouping fields are in scope — the aggregate field (e.g., `WorkItemId`) is not recognized.
   - [Documentation: OData supported features](https://learn.microsoft.com/en-us/azure/devops/report/extend-analytics/odata-supported-features?view=azure-devops)

**Solution** (the library already implements this since F12):

```python
# ✅ CORRECT: aggregate inside groupby, using $count instead of countdistinct
from ado_odata_async.query import Apply, Filter

Apply()
    .filter(Filter.eq("StateCategory", "Completed"))
    .groupby("DateSK", "State")
    .aggregate("$count", alias="Count")
    .build()
# → "$apply=filter(StateCategory eq 'Completed')/groupby((DateSK,State),aggregate($count as Count))"
```

**How to prevent**:
- Never use `countdistinct` as an aggregation method — use `$count` with `alias` for row counting.
- The aggregate is automatically nested inside groupby when they are consecutive in the fluent call.
- If you need distinct counting, use `$count` inside `groupby` with the desired fields in the grouping.

---

## Português (Brasil)

[Português](#english) | **English**

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

**Causa**: O entity set `WorkItemSnapshot` **requer** `$apply` com `groupby`. Um `$filter` simples não é aceito pelo serviço.

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

**Causa**: Duas causas simultâneas:

1. **`countdistinct` é bloqueado pelo ADO Analytics.** A função `countdistinct` existe no OData, mas o Azure DevOps Analytics **não aceita**. A Microsoft afirma que suporte futuro está planejado, mas hoje o uso retorna erro.
   - [Documentação: "DON'T use countdistinct aggregation"](https://learn.microsoft.com/en-us/azure/devops/report/extend-analytics/odata-query-guidelines?view=azure-devops)

2. **`aggregate` deve ser ANINHADO dentro de `groupby`, não encadeado com `/`.** A sintaxe correta do OData é:
   ```
   groupby((State, DateValue), aggregate($count as Count, StoryPoints with sum as TotalStoryPoints))
   ```
   A forma incorreta `groupby((...))/aggregate(...)` gera o erro VS403483 porque, após o `groupby` standalone, apenas os campos de agrupamento estão no escopo — o campo do aggregate (ex.: `WorkItemId`) não é reconhecido.
   - [Documentação: OData supported features](https://learn.microsoft.com/en-us/azure/devops/report/extend-analytics/odata-supported-features?view=azure-devops)

**Solução** (a biblioteca já implementa):

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
- Se precisar de contagem distinta, use `$count` dentro de `groupby` com os campos desejados no agrupamento.
