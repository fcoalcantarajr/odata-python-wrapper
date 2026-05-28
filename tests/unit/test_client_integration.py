"""Integration tests through AdoODataClient.get() — validates wiring
of parse_response, serialize, retry, batch, and typed errors.
"""

from __future__ import annotations

import re

import pytest
from aioresponses import aioresponses

from ado_odata_async import AdoODataClient
from ado_odata_async.auth import build_basic_auth
from ado_odata_async.exceptions import (
    AuthenticationError,
    BadRequestError,
    RateLimitError,
    TransientError,
)
from ado_odata_async.query._batch import (
    build_batch_get_body,
    maybe_batch,
)

# ── auth.build_basic_auth ──────────────────────────────────


def test_build_basic_auth_empty_user() -> None:
    auth = build_basic_auth("pat_xxx")
    assert auth.login == ""


# ── client.get() typed errors via parse_response wiring ────


@pytest.mark.asyncio
async def test_get_401_raises_authentication_error(
    fake_pat: str,
    fake_org: str,
    fake_project: str,
) -> None:
    with aioresponses() as m:
        m.get(
            re.compile(r".*/WorkItems.*"),
            status=401,
            content_type="application/json",
            payload={},
        )
        async with AdoODataClient(
            org=fake_org,
            project=fake_project,
            pat=fake_pat,
        ) as c:
            with pytest.raises(AuthenticationError):
                await c.get("WorkItems")


@pytest.mark.asyncio
async def test_get_203_html_raises_authentication_error(
    fake_pat: str,
    fake_org: str,
    fake_project: str,
) -> None:
    with aioresponses() as m:
        m.get(
            re.compile(r".*/WorkItems.*"),
            status=203,
            content_type="text/html",
            body="<html>Sign in</html>",
        )
        async with AdoODataClient(
            org=fake_org,
            project=fake_project,
            pat=fake_pat,
        ) as c:
            with pytest.raises(AuthenticationError) as exc:
                await c.get("WorkItems")
            assert "203" in str(exc.value)


@pytest.mark.asyncio
async def test_get_400_raises_bad_request_error(
    fake_pat: str,
    fake_org: str,
    fake_project: str,
) -> None:
    with aioresponses() as m:
        m.get(
            re.compile(r".*/WorkItems.*"),
            status=400,
            payload={"error": {"message": "Invalid query option"}},
        )
        async with AdoODataClient(
            org=fake_org,
            project=fake_project,
            pat=fake_pat,
        ) as c:
            with pytest.raises(BadRequestError) as exc:
                await c.get("WorkItems")
            assert "Invalid query option" in str(exc.value)


@pytest.mark.asyncio
async def test_get_502_raises_transient_error(
    fake_pat: str,
    fake_org: str,
    fake_project: str,
) -> None:
    with aioresponses() as m:
        m.get(
            re.compile(r".*/WorkItems.*"),
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
                await c.get("WorkItems")
            assert "502" in str(exc.value)


@pytest.mark.asyncio
async def test_get_429_raises_rate_limit_error(
    fake_pat: str,
    fake_org: str,
    fake_project: str,
) -> None:
    with aioresponses() as m:
        m.get(
            re.compile(r".*/WorkItems.*"),
            status=429,
            headers={"Retry-After": "5"},
            payload={},
            repeat=True,
        )
        async with AdoODataClient(
            org=fake_org,
            project=fake_project,
            pat=fake_pat,
        ) as c:
            with pytest.raises(RateLimitError) as exc:
                await c.get("WorkItems")
            assert "429" in str(exc.value)


# ── canonical serialization via serialize wiring ───────────


@pytest.mark.asyncio
async def test_get_serializes_query_canonical_order(
    fake_pat: str,
    fake_org: str,
    fake_project: str,
) -> None:
    """Verify serialize() is wired to client.get(). aioresponses sorts query params,
    so raw-string order checking is deferred to serialize() unit tests.
    """
    with aioresponses() as m:
        m.get(re.compile(r".*"), payload={"value": []}, repeat=True)

        async with AdoODataClient(
            org=fake_org,
            project=fake_project,
            pat=fake_pat,
        ) as c:
            await c.get("WorkItems", **{"$top": "10", "$filter": "State eq 'Active'"})

    # Verify serialize() was called by checking query params exist
    assert len(m.requests) >= 1
    for _method, url in m.requests:
        qs = url.query_string
        assert "%24top" in qs or "$top" in qs, "Missing $top in query"
        assert "%24filter" in qs or "$filter" in qs, "Missing $filter in query"
        break


# ── maybe_batch with service_root ──────────────────────────


def test_maybe_batch_with_service_root() -> None:
    url = "https://example.com/v4.0-preview/WorkItems?" + "$filter=" + ("x" * 3500)
    method, result_url = maybe_batch(
        "GET", url, threshold=3000, service_root="https://example.com/v4.0-preview"
    )
    assert method == "POST"
    assert result_url == "https://example.com/v4.0-preview/$batch"


def test_maybe_batch_short_url_stays_get() -> None:
    url = "https://example.com/WorkItems"
    method, result_url = maybe_batch(
        "GET", url, threshold=3000, service_root="https://example.com/v4.0-preview"
    )
    assert method == "GET"
    assert result_url == url


# ── build_batch_get_body ───────────────────────────────────


def test_build_batch_get_body_structure() -> None:
    body = build_batch_get_body(
        "https://example.com/v4.0-preview/WorkItems?$filter=State%20eq%20%27Active%27",
        "https://example.com/v4.0-preview",
    )
    assert "GET WorkItems?$filter=State%20eq%20%27Active%27" in body
    assert body.startswith("--batch_ado_odata_async")
    assert body.endswith("--batch_ado_odata_async--\r\n")
    assert "Host: analytics.dev.azure.com" in body
    # No changeset wrapping for GET per OData 4.0 spec
    assert "changeset_ado_odata_async" not in body
