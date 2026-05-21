---
name: async-aiohttp-patterns
description: Padrões seguros pra ClientSession lifecycle, TCPConnector, tenacity retry, e `POST $batch` multipart/mixed. Use quando escrever código em `_http.py`, `client.py`, `retry.py`.
---

# Async aiohttp patterns

## Single ClientSession (HR-7)

```
class AdoODataClient:
	def __init__(self, org: str, project: str, pat: str) -> None:
		self._org = org
		self._project = project
		self._pat = pat
		self._session: aiohttp.ClientSession | None = None

	async def __aenter__(self) -> "AdoODataClient":
		if self._session is not None:
			raise RuntimeError("client already entered")
		connector = aiohttp.TCPConnector(limit=20, limit_per_host=10)
		self._session = aiohttp.ClientSession(
			auth=aiohttp.BasicAuth("", self._pat),  # HR-8
			connector=connector,
			raise_for_status=False,
			timeout=aiohttp.ClientTimeout(total=60),
		)
		return self

	async def __aexit__(self, *exc) -> None:
		assert self._session is not None
		await self._session.close()
		self._session = None
```

## Retry com tenacity (só em retriáveis)

```
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception_type
from ado_odata_async.exceptions import TransientError

@retry(
	stop=stop_after_attempt(4),
	wait=wait_exponential_jitter(initial=0.5, max=8),
	retry=retry_if_exception_type(TransientError),
	reraise=True,
)
async def _do_request(...): ...
```

401/203/4xx (exceto 429) → não-retriável.

## POST $batch multipart/mixed

Quando URL > 3000 chars (HR-10):
```
body = (
	f"--\{boundary\}rn"
	f"Content-Type: application/httprn"
	f"Content-Transfer-Encoding: binaryrnrn"
	f"GET \{path\}?\{qs\} HTTP/1.1rn"
	f"Accept: application/jsonrnrn"
	f"--\{boundary\}--rn"
)
headers = {"Content-Type": f"multipart/mixed; boundary=\{boundary\}"}
async with session.post(batch_url, data=body, headers=headers) as r:
	...
```

## Cancel propagation

- NÃO capture `asyncio.CancelledError` sem re-raise.
- `async with` cleanup garante close mesmo em cancel.
