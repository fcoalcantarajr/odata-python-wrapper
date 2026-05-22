"""Shared fixtures: fake PAT, org/project, parametrizable odata_version."""

from __future__ import annotations

import re
from collections.abc import Iterator

import pytest
from aioresponses import aioresponses


@pytest.fixture
def fake_pat() -> str:
    return "PAT_" + "X" * 50


@pytest.fixture
def fake_org() -> str:
    return "myorg"


@pytest.fixture
def fake_project() -> str:
    return "myproject"


@pytest.fixture(params=["v4.0-preview"])
def odata_version(request: pytest.FixtureRequest) -> str:
    return request.param  # type: ignore[no-any-return]


@pytest.fixture
def base_url(fake_org: str, fake_project: str, odata_version: str) -> str:
    return f"https://analytics.dev.azure.com/{fake_org}" f"/{fake_project}/_odata/{odata_version}"


@pytest.fixture
def mock_http() -> Iterator[aioresponses]:
    with aioresponses() as m:
        # Register catch-all first, then ensure it's always last in _matches
        # so test-specific handlers (registered after yield) take priority.
        # aioresponses 0.7.x uses first-match-wins over _matches dict (ordered).
        m.get(re.compile(r".*"), repeat=True, payload={"value": []})
        catchall_key: str = next(iter(m._matches))

        # Wrap add() so every new registration moves catch-all to end.
        original_add = m.add

        def _add(url, method="GET", **kwargs):  # type: ignore[no-untyped-def]
            original_add(url, method=method, **kwargs)
            if catchall_key in m._matches:
                m._matches[catchall_key] = m._matches.pop(catchall_key)

        m.add = _add  # type: ignore[assignment]
        yield m
