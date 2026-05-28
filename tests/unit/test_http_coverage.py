"""Tests for AS-004: _http.py coverage regression — restore to ≥85%."""

from __future__ import annotations

import aiohttp
import pytest
from aioresponses import aioresponses

from ado_odata_async._http import parse_response
from ado_odata_async.exceptions import (
    AuthenticationError,
    BadRequestError,
    RateLimitError,
)


class TestParseResponse429:
    """AS-004 AC-1 through AC-2: 429 Retry-After parsing."""

    @pytest.mark.asyncio
    async def test_ac1_429_with_valid_retry_after(self) -> None:
        """AC-1: 429 with valid Retry-After header."""
        with aioresponses() as m:
            m.get(
                "https://analytics.dev.azure.com/test/test/_odata/v4.0-preview/WorkItems",
                status=429,
                headers={"Retry-After": "30"},
            )
            async with (
                aiohttp.ClientSession() as session,
                session.get(
                    "https://analytics.dev.azure.com/test/test/_odata/v4.0-preview/WorkItems"
                ) as resp,
            ):
                with pytest.raises(RateLimitError) as exc_info:
                    await parse_response(resp)
                assert exc_info.value.retry_after == 30.0

    @pytest.mark.asyncio
    async def test_ac2_429_with_malformed_retry_after(self) -> None:
        """AC-2: 429 with malformed Retry-After header."""
        with aioresponses() as m:
            m.get(
                "https://analytics.dev.azure.com/test/test/_odata/v4.0-preview/WorkItems",
                status=429,
                headers={"Retry-After": "not-a-number"},
            )
            async with (
                aiohttp.ClientSession() as session,
                session.get(
                    "https://analytics.dev.azure.com/test/test/_odata/v4.0-preview/WorkItems"
                ) as resp,
            ):
                with pytest.raises(RateLimitError) as exc_info:
                    await parse_response(resp)
                assert exc_info.value.retry_after is None


class TestParseResponse203:
    """AS-004 AC-3: 203 + text/html → AuthenticationError."""

    @pytest.mark.asyncio
    async def test_ac3_203_html_raises_authentication_error(self) -> None:
        """AC-3: 203 with text/html content type."""
        with aioresponses() as m:
            m.get(
                "https://analytics.dev.azure.com/test/test/_odata/v4.0-preview/WorkItems",
                status=203,
                body="<html>PAT invalid</html>",
                content_type="text/html",
            )
            async with (
                aiohttp.ClientSession() as session,
                session.get(
                    "https://analytics.dev.azure.com/test/test/_odata/v4.0-preview/WorkItems"
                ) as resp,
            ):
                with pytest.raises(AuthenticationError, match="HTTP 203"):
                    await parse_response(resp)


class TestParseResponse400:
    """AS-004 AC-4 through AC-5: 400 error parsing."""

    @pytest.mark.asyncio
    async def test_ac4_400_with_dict_error(self) -> None:
        """AC-4: 400 with error as dict."""
        with aioresponses() as m:
            m.get(
                "https://analytics.dev.azure.com/test/test/_odata/v4.0-preview/WorkItems",
                status=400,
                payload={"error": {"message": "Bad filter"}},
            )
            async with (
                aiohttp.ClientSession() as session,
                session.get(
                    "https://analytics.dev.azure.com/test/test/_odata/v4.0-preview/WorkItems"
                ) as resp,
            ):
                with pytest.raises(BadRequestError, match="Bad filter"):
                    await parse_response(resp)

    @pytest.mark.asyncio
    async def test_ac5_400_with_string_error(self) -> None:
        """AC-5: 400 with error as string."""
        with aioresponses() as m:
            m.get(
                "https://analytics.dev.azure.com/test/test/_odata/v4.0-preview/WorkItems",
                status=400,
                payload={"error": "Invalid query"},
            )
            async with (
                aiohttp.ClientSession() as session,
                session.get(
                    "https://analytics.dev.azure.com/test/test/_odata/v4.0-preview/WorkItems"
                ) as resp,
            ):
                with pytest.raises(BadRequestError, match="Invalid query"):
                    await parse_response(resp)


class TestParseResponseNonJSON:
    """AS-004 AC-6 through AC-9: Non-JSON responses."""

    @pytest.mark.asyncio
    async def test_ac6_non_json_response(self) -> None:
        """AC-6: Non-JSON response body."""
        with aioresponses() as m:
            m.get(
                "https://analytics.dev.azure.com/test/test/_odata/v4.0-preview/WorkItems",
                status=200,
                body="not json at all",
                content_type="text/plain",
            )
            async with (
                aiohttp.ClientSession() as session,
                session.get(
                    "https://analytics.dev.azure.com/test/test/_odata/v4.0-preview/WorkItems"
                ) as resp,
            ):
                with pytest.raises(BadRequestError, match="Resposta não-JSON"):
                    await parse_response(resp)

    @pytest.mark.asyncio
    async def test_ac7_non_dict_json(self) -> None:
        """AC-7: JSON response that is not a dict."""
        with aioresponses() as m:
            m.get(
                "https://analytics.dev.azure.com/test/test/_odata/v4.0-preview/WorkItems",
                status=200,
                payload=[1, 2, 3],
            )
            async with (
                aiohttp.ClientSession() as session,
                session.get(
                    "https://analytics.dev.azure.com/test/test/_odata/v4.0-preview/WorkItems"
                ) as resp,
            ):
                with pytest.raises(BadRequestError, match="JSON inesperado"):
                    await parse_response(resp)

    @pytest.mark.asyncio
    async def test_ac8_400_with_non_dict_error_value(self) -> None:
        """AC-8: 400 with error as list."""
        with aioresponses() as m:
            m.get(
                "https://analytics.dev.azure.com/test/test/_odata/v4.0-preview/WorkItems",
                status=400,
                payload={"error": [1, 2, 3]},
            )
            async with (
                aiohttp.ClientSession() as session,
                session.get(
                    "https://analytics.dev.azure.com/test/test/_odata/v4.0-preview/WorkItems"
                ) as resp,
            ):
                with pytest.raises(BadRequestError, match="HTTP 400"):
                    await parse_response(resp)

    @pytest.mark.asyncio
    async def test_ac9_400_with_invalid_json_body(self) -> None:
        """AC-9: 400 with invalid JSON body."""
        with aioresponses() as m:
            m.get(
                "https://analytics.dev.azure.com/test/test/_odata/v4.0-preview/WorkItems",
                status=400,
                body="not json",
                content_type="application/json",
            )
            async with (
                aiohttp.ClientSession() as session,
                session.get(
                    "https://analytics.dev.azure.com/test/test/_odata/v4.0-preview/WorkItems"
                ) as resp,
            ):
                with pytest.raises(BadRequestError, match="HTTP 400"):
                    await parse_response(resp)
