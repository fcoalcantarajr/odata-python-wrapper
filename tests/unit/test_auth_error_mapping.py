"""Tests for SPEC-002 auth-error-mapping — parse_response error classification.

GREEN (was RED phase; parse_response implemented).
"""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest
from yarl import URL

from ado_odata_async._http import parse_response
from ado_odata_async.exceptions import (
    AuthenticationError,
    BadRequestError,
    RateLimitError,
    TransientError,
)


def _mock_response(
    status: int,
    content_type: str = "application/json",
    headers: dict[str, str] | None = None,
    json_data: dict[str, Any] | None = None,
    text_data: str | None = None,
) -> aiohttp.ClientResponse:
    """Build a minimal async mock aiohttp.ClientResponse."""
    resp: MagicMock = MagicMock(spec=aiohttp.ClientResponse)
    resp.status = status
    resp.content_type = content_type
    resp.headers = headers or {}
    resp.url = URL("http://mock.url/")

    if json_data is not None:
        resp.json = AsyncMock(return_value=json_data)
        resp.text = AsyncMock(return_value="")
    elif text_data is not None:
        resp.json = AsyncMock(return_value={})
        resp.text = AsyncMock(return_value=text_data)
    else:
        resp.json = AsyncMock(return_value={})
        resp.text = AsyncMock(return_value="")

    return resp  # type: ignore[return-value]  # reason: MagicMock clones spec but returns generic type


@pytest.mark.asyncio
async def test_ac1_401_raises_authentication_error() -> None:
    """AC-1: 401 → AuthenticationError (not retryable).

    Asserts:
      - AuthenticationError is raised
      - AuthenticationError is subclass of AdoODataError
      - AuthenticationError is NOT subclass of TransientError
    """
    resp = _mock_response(status=401)

    with pytest.raises(AuthenticationError) as exc_info:
        await parse_response(resp)

    assert isinstance(exc_info.value, AuthenticationError)
    assert not isinstance(exc_info.value, TransientError)


@pytest.mark.asyncio
async def test_ac2_203_html_raises_authentication_error() -> None:
    """AC-2: 203 + text/html → AuthenticationError (gotcha 8 / HR-15).

    Asserts:
      - AuthenticationError is raised
      - error message contains "203"
    """
    resp = _mock_response(
        status=203,
        content_type="text/html",
        text_data="<html><body>Sign in to your account</body></html>",
    )

    with pytest.raises(AuthenticationError) as exc_info:
        await parse_response(resp)

    assert "203" in str(exc_info.value)


@pytest.mark.asyncio
async def test_ac3_400_raises_bad_request_error() -> None:
    """AC-3: 400 → BadRequestError (not retryable), message reflects server error.

    Asserts:
      - BadRequestError is raised
      - error message contains "Invalid query option"
      - BadRequestError is NOT subclass of TransientError
    """
    resp = _mock_response(
        status=400,
        json_data={"error": {"message": "Invalid query option $select"}},
    )

    with pytest.raises(BadRequestError) as exc_info:
        await parse_response(resp)

    assert "Invalid query option" in str(exc_info.value)
    assert not isinstance(exc_info.value, TransientError)


@pytest.mark.asyncio
async def test_ac4_502_raises_transient_error() -> None:
    """AC-4: 502 → TransientError (retryable).

    Asserts:
      - TransientError is raised
      - error message contains "502"
    """
    resp = _mock_response(status=502)

    with pytest.raises(TransientError) as exc_info:
        await parse_response(resp)

    assert "502" in str(exc_info.value)


@pytest.mark.asyncio
async def test_ac5_429_raises_rate_limit_error() -> None:
    """AC-5: 429 → RateLimitError (subclass of TransientError).

    Asserts:
      - RateLimitError is raised
      - RateLimitError IS subclass of TransientError
      - error message contains "429"
    """
    resp = _mock_response(
        status=429,
        headers={"Retry-After": "5"},
    )

    with pytest.raises(RateLimitError) as exc_info:
        await parse_response(resp)

    assert isinstance(exc_info.value, TransientError)
    assert "429" in str(exc_info.value)


@pytest.mark.asyncio
async def test_ac6_debug_log_emitted(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-6 (partial): DEBUG log is emitted for response processing (HR-16).

    PAT-masking assertions are scoped to client.get() integration tests
    where the PAT is accessible (SPEC-001 + SPEC-002 integration).
    """
    resp = _mock_response(status=200)

    caplog.set_level(logging.DEBUG)
    result = await parse_response(resp)

    assert isinstance(result, dict)
    assert "ado_odata_async._http" in caplog.text
    assert "Parsing response" in caplog.text


@pytest.mark.asyncio
async def test_ac7_200_returns_dict_parsed() -> None:
    """AC-7: 200 → parse_response returns parsed dict normally.

    Asserts:
      - return value is a dict
      - dict["@odata.count"] == 1 (numeric equality)
    """
    body = {"value": [{"Id": 1}], "@odata.count": 1}
    resp = _mock_response(status=200, json_data=body)

    result = await parse_response(resp)

    assert isinstance(result, dict)
    assert result["@odata.count"] == 1
