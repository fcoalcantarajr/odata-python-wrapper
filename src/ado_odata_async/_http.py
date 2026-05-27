"""Low-level HTTP helpers (response parsing)."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from ado_odata_async.exceptions import (
    AuthenticationError,
    BadRequestError,
    RateLimitError,
    TransientError,
)

logger = logging.getLogger(__name__)


async def parse_response(resp: aiohttp.ClientResponse) -> dict[str, Any]:
    """Parse JSON response, mapping HTTP errors to typed exceptions (HR-15).

    Error → exception mapping (gotchas 1, 8):
      - 203 + text/html → AuthenticationError (PAT inválido, não retry)
      - 401            → AuthenticationError (não retry)
      - 400            → BadRequestError (não retry)
      - 429            → RateLimitError (retry cap 3)
      - 5xx            → TransientError (retry com backoff)
    """
    logger.debug("Parsing response: HTTP %s %s", resp.status, resp.content_type)

    if resp.status == 203 and resp.content_type == "text/html":
        text = await resp.text()
        raise AuthenticationError(
            f"HTTP 203 non-JSON: PAT inválido ou expirado. " f"Response: {text[:200]}"
        )

    if resp.status == 401:
        raise AuthenticationError("HTTP 401: PAT inválido ou sem permissão")

    if resp.status == 400:
        try:
            body = await resp.json()
            error_val = body.get("error")
            if isinstance(error_val, dict):
                msg = error_val.get("message", "HTTP 400: Bad request")
            elif isinstance(error_val, str):
                msg = error_val
            else:
                msg = "HTTP 400: Bad request"
        except (ValueError, aiohttp.ContentTypeError) as exc:
            logger.debug("Failed to parse 400 response body: %s", exc)
            msg = "HTTP 400: Bad request"
        raise BadRequestError(msg)

    if resp.status == 429:
        raw = resp.headers.get("Retry-After", "0")
        try:
            retry_after = float(raw)
        except ValueError:
            logger.debug("Retry-After header malformed or non-numeric: %r, using None", raw)
            retry_after = None
        raise RateLimitError(
            f"HTTP 429: Rate limit. Retry-After: {raw}s",
            retry_after=retry_after,
        )

    if 500 <= resp.status < 600:
        raise TransientError(f"HTTP {resp.status}: Erro transitório do servidor")

    try:
        body = await resp.json()
    except (ValueError, aiohttp.ContentTypeError) as exc:
        text = await resp.text()
        raise BadRequestError(f"HTTP {resp.status}: Resposta não-JSON: {text[:200]}") from exc
    if not isinstance(body, dict):
        raise BadRequestError(f"HTTP {resp.status}: JSON inesperado: tipo {type(body).__name__}")
    return body
