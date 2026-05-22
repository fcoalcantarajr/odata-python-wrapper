"""URL length check and $batch switch per HR-10.

If URL exceeds threshold (default 3000), switch from GET to POST $batch.
Multipart/mixed response parser for the ADO Analytics batch format.

Pure sync functions — no async, no aiohttp, no external deps beyond stdlib.
"""

from __future__ import annotations

import json
import re
from typing import cast


def maybe_batch(method: str, url: str, threshold: int = 3000) -> tuple[str, str]:
    """Decide whether to switch to POST $batch based on URL length.

    If ``len(url) > threshold``, switch to ``POST`` with a ``/$batch``
    suffix appended to the URL.  Otherwise return ``(method, url)``
    unchanged.

    Parameters
    ----------
    method:
        Original HTTP method (e.g. ``"GET"``).
    url:
        Full request URL including query string.
    threshold:
        URL length threshold in characters (default ``3000`` per HR-10).

    Returns
    -------
    tuple[str, str]
        ``(http_method, url)`` — either the original pair or switched to
        ``("POST", url + "/$batch")``.
    """
    if len(url) > threshold:
        return ("POST", url.rstrip("/") + "/$batch")
    return (method, url)


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
