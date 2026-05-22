"""Coverage for pre-existing stubs (SPEC-002+). These tests verify the API surface
exists and raise NotImplementedError — they will be replaced by real tests when
each spec is implemented.
"""

from __future__ import annotations

import pytest

from ado_odata_async import _http, entities, metadata, pagination, query, retry
from ado_odata_async.entities._base import ODataEntity


@pytest.mark.asyncio
async def test_parse_response_stub() -> None:
    """parse_response currently raises NotImplementedError (SPEC-002)."""
    with pytest.raises(NotImplementedError):
        await _http.parse_response(None)  # type: ignore[arg-type]  # reason: stub ignores arg


@pytest.mark.asyncio
async def test_fetch_metadata_stub() -> None:
    """fetch_metadata currently raises NotImplementedError (SPEC-012)."""
    with pytest.raises(NotImplementedError):
        await metadata.fetch_metadata(None)  # type: ignore[arg-type]  # reason: stub ignores arg


@pytest.mark.asyncio
async def test_iter_pages_stub() -> None:
    """iter_pages currently raises NotImplementedError (SPEC-004)."""
    gen = pagination.iter_pages(None, "")  # type: ignore[arg-type]  # reason: stub
    with pytest.raises(NotImplementedError):
        await gen.__anext__()


@pytest.mark.asyncio
async def test_with_retry_stub() -> None:
    """with_retry currently raises NotImplementedError (SPEC-003)."""
    with pytest.raises(NotImplementedError):
        await retry.with_retry(lambda: None)()  # type: ignore[arg-type]  # reason: stub ignores sig


def test_entities_module_importable() -> None:
    """entities module is importable with ODataEntity base."""
    assert entities is not None
    assert ODataEntity.model_config.get("populate_by_name") is True


def test_query_module_importable() -> None:
    """query module is importable."""
    assert query is not None
    assert isinstance(query.__all__, list)
