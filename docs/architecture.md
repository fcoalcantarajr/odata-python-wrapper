<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# Architecture

## Camadas

1. **Auth** (`auth.py`) — PAT → BasicAuth(empty user). Mask helpers.
2. **HTTP transport** (`_http.py`) — URL building (canonical query order), response parsing, $batch.
3. **Client** (`client.py`) — Lifecycle de ClientSession (single instance, HR-7). Top-level API.
4. **Retry** (`retry.py`) — tenacity wrapper, retriável só em TransientError.
5. **Query** (`query/`) — DSL pra `$filter`, `$apply`, etc; serializer emite ordem canônica.
6. **Pagination** (`pagination.py`) — async iterator over `$skip` pages.
7. **Metadata** (`metadata.py`) — fetch + cache de `$metadata`.
8. **Entities** (`entities/`) — Pydantic models frozen+strict, um módulo por entity set.
9. **Exceptions** (`exceptions.py`) — hierarquia: AdoODataError -> {AuthenticationError, BadRequestError, TransientError -> RateLimitError}.

## Fluxo de uma chamada

```
user code
	-> AdoODataClient.\<method\>
		-> query/_serialize (canonical order, HR-9)
			-> _http.build_url (HR-19 v4.0-preview)
				-> retry wrapper (HR-15)
					-> session.get / post
						-> _http.parse_response (HR-15 203 detection)
							-> entities.\<Entity\>(row)  (Pydantic frozen+strict, HR-4)
	\<- async iterator / list
```

## Decisões chave

- `ODATA_VERSION = "v4.0-preview"` em `client.py` é single source of truth (HR-19/HR-20).
- Single ClientSession (HR-7) cria-se em `__aenter__`, fecha em `__aexit__`.
- Tenacity decorator centralizado em `retry.py` (HR-15); 401/203 nunca retriáveis.
- Query options serializadas pelo módulo `query/_serialize.py` (HR-9); usuario nunca constrói URL mão.
