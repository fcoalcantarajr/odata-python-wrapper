1: <!-- notion-page-id: -->
2: <!-- last-sync-hash: -->
3: 
4: # Architecture
5: 
6: ## Camadas
7: 
8: 1. **Auth** (`auth.py`) — PAT → BasicAuth(empty user). Mask helpers.
9: 2. **HTTP transport** (`_http.py`) — response parsing, error mapping.
10: 3. **Client** (`client.py`) — Lifecycle de ClientSession (single instance, HR-7). Top-level API.
11: 4. **Retry** (`retry.py`) — tenacity wrapper, retriável só em TransientError.
12: 5. **Query** (`query/`) — DSL pra `$filter`, `$apply`, etc; serializer emite ordem canônica.
13: 6. **Pagination** (`pagination.py`) — async iterator over `$skip` pages.
14: 7. **Metadata** (`metadata.py`) — fetch + cache de `$metadata`.
15: 8. **Entities** (`entities/`) — Pydantic models frozen+strict, um módulo por entity set.
16: 9. **Batch** (`query/_batch.py`) — URL > 3000 chars → switch pra `POST $batch` multipart/mixed (HR-10).
17: 10. **Fluent API** (`query/_builder.py`) — QueryBuilder imutável que compõe Filter, Apply, select, top, skip, orderby, expand (SPEC-011).
18: 11. **Exceptions** (`exceptions.py`) — hierarquia: AdoODataError -> {AuthenticationError, BadRequestError, TransientError -> RateLimitError}.
19: 
20: ## Fluxo de uma chamada
21: 
22: ### Simple GET (via builder)
23: 
24: ```
25: user code
26:   -> client.query("WorkItems").filter(...).select(...).top(10)
27:     -> QueryBuilder.__str__() via query/_serialize (canonical order HR-9)
28:   -> await builder.get()
29:       -> AdoODataClient.get(entity_set, **params)
30:        -> query/_serialize (canonical order HR-9)
31:        -> retry wrapper (HR-15)
32:          -> aiohttp session.get (URL via f-string service_root)
33:            -> _http.parse_response (HR-15 203 detection)
34:     <- dict response
35: ```
36: 
37: ### Pagination
38: 
39: ```
40: user code
41:   -> async for page in client.paginate("WorkItems", query=...):
42:     -> iter_pages (calcula $skip ou segue @odata.nextLink)
43:       -> client.get(entity_set, **merged_query)
44:         -> mesmo fluxo GET acima
45:     <- dict[value=items]
46: ```
47: 
48: ### Batch (URL > 3000 chars)
49: 
50: ```
51: client.get(entity_set, **params)
52:   -> maybe_batch(serialized_query)
53:     -> if len > 3000:
54:       -> POST $batch multipart/mixed (changeset com GET embutido)
55:         -> parse_batch_response (extrai JSON do multipart)
56:     <- else: GET normal
57: ```
58: 
59: ## Decisões chave
60: 
61: - `ODATA_VERSION = "v4.0-preview"` em `client.py` é single source of truth (HR-19/HR-20).
62: - Single ClientSession (HR-7) cria-se em `__aenter__`, fecha em `__aexit__`.
63: - Tenacity decorator centralizado em `retry.py` (HR-15); 401/203 nunca retriáveis.
64: - Query options serializadas pelo módulo `query/_serialize.py` (HR-9); usuario nunca constrói URL mão.
65: - Builders imutáveis: Filter e QueryBuilder retornam novas instâncias em cada chain.
66: - Pydantic frozen+strict+extra-forbid em todas entidades (ADR-006).
