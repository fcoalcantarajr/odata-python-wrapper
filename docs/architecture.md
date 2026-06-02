**English** | [Português](#português-brasil)

# Architecture

## Layers

1. **Auth** (`auth.py`) — converts PAT to BasicAuth (empty username). Mask helpers for safe logging.
2. **HTTP transport** (`_http.py`) — response parsing, error mapping.
3. **Client** (`client.py`) — manages the `ClientSession` lifecycle (single instance). Top-level API.
4. **Retry** (`retry.py`) — tenacity wrapper, retries only on `TransientError`.
5. **Query** (`query/`) — DSL for `$filter`, `$apply`, etc; serializer emits canonical order.
6. **Pagination** (`pagination.py`) — async iterator over `$skip` pages.
7. **Metadata** (`metadata.py`) — fetch + cache of `$metadata`.
8. **Entities** (`entities/`) — Pydantic models (frozen + strict), one module per entity set.
9. **Batch** (`query/_batch.py`) — URL > 3000 chars → switches to `POST $batch` multipart/mixed.
10. **Fluent API** (`query/_builder.py`) — immutable `QueryBuilder` composing Filter, Apply, select, top, skip, orderby, expand.
11. **Exceptions** (`exceptions.py`) — hierarchy: `AdoODataError` → {`AuthenticationError`, `BadRequestError`, `TransientError` → `RateLimitError`}.

## Call flow

### Simple GET (via builder)

```
user code
  -> client.query("WorkItems").filter(...).select(...).top(10)
    -> QueryBuilder.__str__() via query/_serialize (canonical order)
  -> await builder.get()
      -> AdoODataClient.get(entity_set, **params)
       -> query/_serialize (canonical order)
       -> retry wrapper
         -> aiohttp session.get (URL via f-string service_root)
           -> _http.parse_response (203 detection)
    <- dict response
```

### Pagination

```
user code
  -> async for page in client.paginate("WorkItems", query=...):
    -> iter_pages (calculates $skip or follows @odata.nextLink)
      -> client.get(entity_set, **merged_query)
        -> same GET flow as above
    <- dict[value=items]
```

### Batch (URL > 3000 chars)

```
client.get(entity_set, **params)
  -> maybe_batch(serialized_query)
    -> if len > 3000:
      -> POST $batch multipart/mixed (changeset with embedded GET)
        -> parse_batch_response (extracts JSON from multipart)
    <- else: normal GET
```

## Key design decisions

- `ODATA_VERSION = "v4.0-preview"` in `client.py` is the single source of truth.
- Single `ClientSession` — created in `__aenter__`, closed in `__aexit__`.
- Tenacity decorator centralized in `retry.py`; 401/203 are never retried.
- Query options serialized by `query/_serialize.py`; you never build URLs by hand.
- Immutable builders: Filter and QueryBuilder return new instances on each chain.
- Pydantic frozen + strict + extra-forbid on all entities.

---

## Português (Brasil)

[Português](#english) | **English**

# Arquitetura

## Camadas

1. **Auth** (`auth.py`) — converte PAT para BasicAuth (username vazio). Helpers de mascaramento para logs seguros.
2. **HTTP transport** (`_http.py`) — parsing de respostas, mapeamento de erros.
3. **Client** (`client.py`) — gerencia o ciclo de vida do `ClientSession` (instância única). API de alto nível.
4. **Retry** (`retry.py`) — wrapper do tenacity, retenta apenas em `TransientError`.
5. **Query** (`query/`) — DSL para `$filter`, `$apply`, etc; serializador emite ordem canônica.
6. **Pagination** (`pagination.py`) — iterador assíncrono sobre páginas `$skip`.
7. **Metadata** (`metadata.py`) — busca + cache de `$metadata`.
8. **Entities** (`entities/`) — modelos Pydantic (frozen + strict), um módulo por entity set.
9. **Batch** (`query/_batch.py`) — URL > 3000 chars → muda para `POST $batch` multipart/mixed.
10. **Fluent API** (`query/_builder.py`) — `QueryBuilder` imutável compondo Filter, Apply, select, top, skip, orderby, expand.
11. **Exceptions** (`exceptions.py`) — hierarquia: `AdoODataError` → {`AuthenticationError`, `BadRequestError`, `TransientError` → `RateLimitError`}.

## Fluxo de uma chamada

### Simple GET (via builder)

```
código do usuário
  -> client.query("WorkItems").filter(...).select(...).top(10)
    -> QueryBuilder.__str__() via query/_serialize (ordem canônica)
  -> await builder.get()
      -> AdoODataClient.get(entity_set, **params)
       -> query/_serialize (ordem canônica)
       -> retry wrapper
         -> aiohttp session.get (URL via f-string service_root)
           -> _http.parse_response (detecção de 203)
    <- dict response
```

### Paginação

```
código do usuário
  -> async for page in client.paginate("WorkItems", query=...):
    -> iter_pages (calcula $skip ou segue @odata.nextLink)
      -> client.get(entity_set, **merged_query)
        -> mesmo fluxo GET acima
    <- dict[value=items]
```

### Batch (URL > 3000 chars)

```
client.get(entity_set, **params)
  -> maybe_batch(serialized_query)
    -> if len > 3000:
      -> POST $batch multipart/mixed (changeset com GET embutido)
        -> parse_batch_response (extrai JSON do multipart)
    <- else: GET normal
```

## Decisões de design importantes

- `ODATA_VERSION = "v4.0-preview"` em `client.py` é a única fonte de verdade.
- `ClientSession` único — criado em `__aenter__`, fechado em `__aexit__`.
- Decorator do tenacity centralizado em `retry.py`; 401/203 nunca são retentados.
- Opções de query serializadas por `query/_serialize.py`; você nunca constrói URLs na mão.
- Builders imutáveis: Filter e QueryBuilder retornam novas instâncias a cada chain.
- Pydantic frozen + strict + extra-forbid em todas as entidades.
