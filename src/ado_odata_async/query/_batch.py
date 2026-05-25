"""URL length check and $batch switch per HR-10.

If URL exceeds threshold (default 3000), switch from GET to POST $batch.
Multipart/mixed response parser for the ADO Analytics batch format.

Pure sync functions — no async, no aiohttp, no external deps beyond stdlib.
"""

from __future__ import annotations

import json
import re
from typing import cast

# Fixed boundary for batch requests. Using a constant makes testing
# and content-type header construction simpler. The actual boundary
# value doesn't matter as long as it doesn't appear in the body.
_BATCH_BOUNDARY = "batch_ado_odata_async"

_BATCH_CONTENT_TYPE = f"multipart/mixed; boundary={_BATCH_BOUNDARY}"


def maybe_batch(
    method: str,
    url: str,
    threshold: int = 3000,
    service_root: str | None = None,
) -> tuple[str, str]:
    """Decide whether to switch to POST $batch based on URL length.

    If ``len(url) > threshold``, switch to ``POST`` with the batch
    endpoint at ``service_root/$batch``.  Otherwise return ``(method, url)``
    unchanged.

    Parameters
    ----------
    method:
        Original HTTP method (e.g. ``"GET"``).
    url:
        Full request URL including query string.
    threshold:
        URL length threshold in characters (default ``3000`` per HR-10).
    service_root:
        OData service root URL (e.g. ``https://.../v4.0-preview/``).
        Required for correct ``/$batch`` endpoint construction.
        If omitted (legacy callers), falls back to appending to *url*.

    Returns
    -------
    tuple[str, str]
        ``(http_method, url)`` — either the original pair or switched to
        ``("POST", service_root + "/$batch")``.
    """
    if len(url) > threshold:
        if service_root:
            return ("POST", service_root.rstrip("/") + "/$batch")
        return ("POST", url.rstrip("/") + "/$batch")
    return (method, url)


def build_batch_get_body(query_url: str, service_root: str) -> str:
    """Build the multipart/mixed body for a GET request via ``$batch``.

    Constructs a minimal OData batch request with a single GET request
    part directly under the batch boundary (no changeset wrapping — those
    are for CUD operations only, per OData 4.0 spec).

    Parameters
    ----------
    query_url:
        Full request URL including query string.
    service_root:
        OData service root URL.

    Returns
    -------
    str
        The multipart/mixed body string, ready to be encoded to ``utf-8``.
    """
    # Derive the relative URL from the service root
    prefix = service_root.rstrip("/") + "/"
    relative = query_url[len(prefix):] if query_url.startswith(prefix) else query_url

    body = (
        f"--{_BATCH_BOUNDARY}\r\n"
        f"Content-Type: application/http\r\n"
        f"Content-Transfer-Encoding: binary\r\n"
        f"\r\n"
        f"GET {relative} HTTP/1.1\r\n"
        f"Host: analytics.dev.azure.com\r\n"
        f"\r\n"
        f"--{_BATCH_BOUNDARY}--\r\n"
    )
    return body


def parse_batch_response(raw: bytes) -> dict[str, object]:
    """Extract JSON dict from a multipart/mixed ``$batch`` response.

    Handles the ADO Analytics batch response format::

        --batchresponse_<boundary>
        Content-Type: application/http
        Content-Transfer-Encoding: binary

        HTTP/1.1 200 OK
        Content-Type: application/json

        {"@odata.context": "...", "value": [...]}
        --batchresponse_<boundary>--

    Parameters
    ----------
    raw:
        Raw bytes of the multipart/mixed response body.

    Returns
    -------
    dict
        Parsed JSON dict from the inner HTTP 200 response body.

    Raises
    ------
    ValueError
        If no HTTP 200 JSON part is found in the response.
    """
    text = raw.decode("utf-8")

    # Split multipart body by boundary markers.
    # Matches e.g. ``\r\n--batchresponse_abc123`` or ``\r\n--batchresponse_abc123--``
    parts = re.split(r"\r?\n--[^\r\n]*", text)

    for part in parts:
        part = part.strip()
        if not part:
            continue
        if "HTTP/1.1 200 OK" in part or "HTTP/1.1 200" in part:
            # Locate the JSON body after the blank line that follows HTTP headers
            match = re.search(r"\r?\n\r?\n(\{.*\})", part, re.DOTALL)
            if match:
                return cast(dict[str, object], json.loads(match.group(1)))

    raise ValueError("No HTTP 200 JSON part found in batch response")
