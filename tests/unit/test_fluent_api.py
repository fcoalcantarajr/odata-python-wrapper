"""GREEN-phase tests for SPEC-011 Fluent API QueryBuilder."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from ado_odata_async.query._builder import QueryBuilder
from ado_odata_async.query._filter import Filter


class _MockClient:
    """Minimal mock client for builder.get/paginate tests."""

    def __init__(self) -> None:
        self.get_calls: list[tuple[str, dict[str, str]]] = []
        self.paginate_calls: list[tuple[str, int, dict[str, str] | None]] = []

    async def get(self, entity_set: str, **params: str) -> dict:
        self.get_calls.append((entity_set, params))
        return {"value": [{"Id": 1, "Title": "Bug A"}]}

    def paginate(
        self,
        entity_set: str,
        *,
        top: int = 100,
        query: dict[str, str] | None = None,
    ) -> AsyncIterator[dict]:
        self.paginate_calls.append((entity_set, top, query))

        async def _pages() -> AsyncIterator[dict]:
            yield {"value": [{"Id": 1}, {"Id": 2}]}
            yield {"value": [{"Id": 3}]}

        return _pages()


def test_ac1_empty_builder() -> None:
    builder = QueryBuilder()
    assert str(builder) == ""


def test_ac2_serialization() -> None:
    builder = (
        QueryBuilder()
        .filter(Filter.eq("State", "Active"))
        .select("Title", "State")
        .top(10)
    )
    expected = "$filter=State%20eq%20%27Active%27&$select=Title%2CState&$top=10"
    assert str(builder) == expected


@pytest.mark.asyncio
async def test_ac3_get_executes() -> None:
    client = _MockClient()
    builder = QueryBuilder(client=client, entity_set="WorkItems")
    result = await builder.get()
    assert result == {"value": [{"Id": 1, "Title": "Bug A"}]}
    assert len(client.get_calls) == 1
    assert client.get_calls[0] == ("WorkItems", {})


@pytest.mark.asyncio
async def test_ac4_paginate() -> None:
    client = _MockClient()
    builder = QueryBuilder(client=client, entity_set="WorkItems")
    pages = []
    async for page in builder.paginate():
        pages.append(page)
    assert len(pages) == 2
    assert pages[0] == {"value": [{"Id": 1}, {"Id": 2}]}
    assert pages[1] == {"value": [{"Id": 3}]}


def test_ac5_immutability() -> None:
    b1 = QueryBuilder()
    b2 = b1.top(10)
    assert str(b1) == ""
    assert str(b2) == "$top=10"


# ── remaining chainable setters ────────────────────────────


class _FakeApply:
    """Minimal stand-in for Apply in builder.apply()."""

    def build(self) -> str:
        return "groupby((DateSK))"


def test_apply_clause() -> None:
    builder = QueryBuilder().apply(_FakeApply())
    assert str(builder) == "$apply=groupby%28%28DateSK%29%29"


def test_orderby_clause() -> None:
    builder = QueryBuilder().orderby("WorkItemId desc", "Title asc")
    assert str(builder) == "$orderby=WorkItemId%20desc%2CTitle%20asc"


def test_expand_clause() -> None:
    builder = QueryBuilder().expand("Children", "Parent")
    assert str(builder) == "$expand=Children%2CParent"


def test_skip_clause() -> None:
    builder = QueryBuilder().skip(20)
    assert str(builder) == "$skip=20"


# ── repr ───────────────────────────────────────────────────


def test_repr_empty() -> None:
    builder = QueryBuilder()
    r = repr(builder)
    assert "entity_set='(none)'" in r
    assert "clauses=[]" in r


def test_repr_with_clauses() -> None:
    builder = QueryBuilder(entity_set="WorkItems").filter(Filter.eq("State", "Active")).top(10)
    r = repr(builder)
    assert "entity_set='WorkItems'" in r
    assert "$filter" in r
    assert "$top" in r


# ── error cases ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_without_client_raises() -> None:
    builder = QueryBuilder()
    with pytest.raises(RuntimeError, match="requires client and entity_set"):
        await builder.get()


def test_paginate_without_client_raises() -> None:
    builder = QueryBuilder()
    with pytest.raises(RuntimeError, match="requires client and entity_set"):
        builder.paginate()


def test_paginate_invalid_top_raises() -> None:
    client = _MockClient()
    builder = QueryBuilder(client=client, entity_set="WorkItems")
    with pytest.raises(ValueError, match="top must be >= 1"):
        builder.paginate(top=0)
