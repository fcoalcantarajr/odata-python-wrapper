"""Tests for AS-104: Batch POST path coverage (AC-1 to AC-3).

These tests exercise the code paths in ``client.get()`` that are triggered
when the serialized URL exceeds 3000 characters and the request is switched
to a ``POST $batch`` call.

The URL threshold is hit by using a long ``$filter`` string.
"""

from __future__ import annotations

import re
from unittest.mock import patch

import aiohttp
import pytest
from aioresponses import aioresponses

from ado_odata_async import AdoODataClient
from ado_odata_async.exceptions import BadRequestError, TransientError

# A filter string long enough to push the full URL over 3000 characters.
# Base URL: ~90 chars + "/WorkItems?" + "$filter=" (9) + this = > 3000
_LONG_FILTER: str = "x" * 2950


# ── AC-1: Batch POST non-200 raises typed error through client.get() ──


@pytest.mark.asyncio
async def test_ac1_batch_post_400_raises_bad_request_error(
    fake_pat: str,
    fake_org: str,
    fake_project: str,
) -> None:
    """AC-1: Batch POST 400 → BadRequestError with message."""
    with aioresponses() as m:
        m.post(
            re.compile(r".*/\$batch"),
            status=400,
            payload={"error": {"message": "bad filter"}},
        )
        async with AdoODataClient(
            org=fake_org,
            project=fake_project,
            pat=fake_pat,
        ) as c:
            with pytest.raises(BadRequestError) as exc:
                await c.get("WorkItems", **{"$filter": _LONG_FILTER})
            assert "bad filter" in str(exc.value)


# ── AC-2: aiohttp.ClientError in batch POST raises TransientError ──


@pytest.mark.asyncio
async def test_ac2_client_error_raises_transient_error(
    fake_pat: str,
    fake_org: str,
    fake_project: str,
) -> None:
    """AC-2: aiohttp.ClientError in batch POST → TransientError.

    The ``@with_retry`` decorator retries 3 times, so the mock must
    raise ``ClientError`` on every attempt.
    """
    client_error = aiohttp.ClientError("connection reset")

    async with AdoODataClient(
        org=fake_org,
        project=fake_project,
        pat=fake_pat,
    ) as c:
        # Patch the client's internal session so the POST raises
        # ClientError deterministically on every retry.
        with patch.object(c, "_session") as mock_session:
            mock_session.post.side_effect = client_error

            with pytest.raises(TransientError) as exc:
                await c.get("WorkItems", **{"$filter": _LONG_FILTER})
            assert "connection reset" in str(exc.value)
            assert exc.value.__cause__ is client_error


# ── AC-3: Non-snapshot entity batch POST 502 raises TransientError ──


@pytest.mark.asyncio
async def test_ac3_batch_post_502_raises_transient_error(
    fake_pat: str,
    fake_org: str,
    fake_project: str,
) -> None:
    """AC-3: Batch POST 502 for non-snapshot entity → TransientError."""
    with aioresponses() as m:
        # Mock the POST $batch to return 502. The retry decorator
        # will retry, so mark it repeatable.
        m.post(
            re.compile(r".*/\$batch"),
            status=502,
            payload={},
            repeat=True,
        )
        async with AdoODataClient(
            org=fake_org,
            project=fake_project,
            pat=fake_pat,
        ) as c:
            with pytest.raises(TransientError) as exc:
                await c.get("WorkItems", **{"$filter": _LONG_FILTER})
            assert "502" in str(exc.value)
