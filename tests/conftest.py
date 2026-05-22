"""Shared fixtures: fake PAT, org/project, parametrizable odata_version."""

from __future__ import annotations

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
        yield m
