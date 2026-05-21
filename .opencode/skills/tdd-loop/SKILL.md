---
name: tdd-loop
description: Loop RED -> GREEN -> REFACTOR pra Python async com aiohttp + aioresponses + pytest-asyncio. Use quando escrever teste antes de impl, quando montar `tests/conftest.py`, ou quando refatorar código já GREEN.
---

# TDD loop

## When to use

- Antes de tocar `src/`: sempre teste primeiro (HR-3).
- Em `/test-first` (RED), `/implement` (GREEN), refactor (manter GREEN).

## Ciclo

```
RED   → escreve teste que falha (motivo claro: NotImplementedError ou AssertionError)
GREEN → escreve código mínimo que faz o teste passar
REFACTOR → melhora código SEM mudar o que os testes verificam
```

## Anatomia de teste aiohttp

```
import pytest
from aioresponses import aioresponses
from ado_odata_async import AdoODataClient

@pytest.mark.asyncio
async def test_ac1_session_reuse_v4_preview(fake_pat: str) -> None:
	"""AC-1: same ClientSession across calls on v4.0-preview endpoint."""
	with aioresponses() as m:
		url = "https://analytics.dev.azure.com/myorg/myproject/_odata/v4.0-preview/WorkItems"
		m.get(url, payload={"value": []}, repeat=True)
		async with AdoODataClient(org="myorg", project="myproject", pat=fake_pat) as c:
			s1 = c._session
			await c.get("WorkItems")
			await c.get("WorkItems")
			s2 = c._session
			assert s1 is s2  # HR-7
```

## Fixture canon (tests/conftest.py)

```
import pytest
from aioresponses import aioresponses

@pytest.fixture
def fake_pat() -> str:
	return "PAT_" + "X" * 50  # marcador test-only

@pytest.fixture
def fake_org() -> str:
	return "myorg"

@pytest.fixture
def fake_project() -> str:
	return "myproject"

@pytest.fixture(params=["v4.0-preview"])
def odata_version(request) -> str:
	return request.param

@pytest.fixture
def base_url(fake_org: str, fake_project: str, odata_version: str) -> str:
	return f"https://analytics.dev.azure.com/{fake_org}/{fake_project}/_odata/{odata_version}"

@pytest.fixture
def mock_http():
	with aioresponses() as m:
		yield m
```

## Anti-cheats (evitar)

- `assert True` ou `assert 1 == 1` → reject.
- `time.sleep(...)` em teste async → use `await asyncio.sleep(0)` ou nada.
- Mock que aceita qualquer argumento → prefira `aioresponses` que valida URL exata.
- Teste sem `await` em código async → esquecimento; sempre check.
