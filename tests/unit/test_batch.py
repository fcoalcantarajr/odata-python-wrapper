"""Tests for SPEC-008 POST $batch URL length switch per HR-10.

GREEN (was RED phase; maybe_batch implemented).

Pure sync tests — no async, no fixtures needed, no mocking.

Each test maps to one AC from specs/008-batch-post.md:
  - AC-1: URL <= threshold -> GET unchanged
  - AC-2: URL > threshold -> POST $batch
  - AC-3: $batch response parsed correctly
  - AC-4: Configurable threshold
  - AC-5: Exact threshold -> GET
"""

from __future__ import annotations

from ado_odata_async.query._batch import maybe_batch, parse_batch_response


def test_ac1_short_url_uses_get() -> None:
    """AC-1: URL <= threshold returns (method, url) unchanged.

    ``maybe_batch("GET", "https://example.com/WorkItems", threshold=3000)``
    with a URL of 42 chars (well under 3000) returns ``("GET", url)``
    — no change to method or URL.
    """
    url = "https://example.com/WorkItems"
    method, result_url = maybe_batch("GET", url, threshold=3000)
    assert method == "GET"
    assert result_url == url


def test_ac2_long_url_uses_post_batch() -> None:
    """AC-2: URL > threshold switches to POST $batch.

    ``maybe_batch("GET", long_url, threshold=3000)`` where
    ``len(long_url)`` > 3000 returns ``("POST", batch_url)`` where
    ``batch_url`` ends with ``"/$batch"``.
    """
    base = "https://example.com/WorkItems?" + "$filter=" + ("x" * 3500)
    assert len(base) > 3000
    method, result_url = maybe_batch("GET", base, threshold=3000)
    assert method == "POST"
    assert result_url.endswith("/$batch")


def test_ac3_batch_response_parsed() -> None:
    """AC-3: Multipart/mixed batch response is parsed to dict.

    ``parse_batch_response(raw_bytes)`` given a valid multipart/mixed
    body with one HTTP 200 JSON part returns a ``dict`` containing
    keys ``@odata.context`` and ``value``.

    The raw payload is constructed to mimic a real ADO Analytics
    $batch response with boundary ``batchresponse_abc123``.
    """
    raw = (
        b"--batchresponse_abc123\r\n"
        b"Content-Type: application/http\r\n"
        b"Content-Transfer-Encoding: binary\r\n"
        b"\r\n"
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: application/json\r\n"
        b"\r\n"
        b'{"@odata.context": "https://analytics.dev.azure.com/'
        b"myorg/myproject/_odata/v4.0-preview/"
        b'$metadata#WorkItems",'
        b'"value": [{"WorkItemId": 1, "Title": "Bug"}]}\r\n'
        b"--batchresponse_abc123--\r\n"
    )
    result = parse_batch_response(raw)
    assert isinstance(result, dict)
    assert "@odata.context" in result
    assert "value" in result
    assert result["value"] == [{"WorkItemId": 1, "Title": "Bug"}]


def test_ac4_configurable_threshold() -> None:
    """AC-4: Lower threshold triggers POST for same URL.

    ``maybe_batch("GET", url, threshold=500)`` with a 2000-char URL
    returns POST because 2000 > 500 — the threshold is configurable
    and a lower value makes the switch trigger earlier.
    """
    url = "https://example.com/WorkItems?" + "$filter=" + ("y" * 1962)
    assert len(url) == 2000  # 30 chars base + "y" * 1962 + "$filter="
    method, result_url = maybe_batch("GET", url, threshold=500)
    assert method == "POST"
    assert result_url.endswith("/$batch")


def test_ac5_exact_threshold_uses_get() -> None:
    """AC-5: URL exactly equal to threshold stays GET.

    ``maybe_batch("GET", url, threshold=3000)`` where
    ``len(url) == 3000`` returns ``("GET", url)`` unchanged —
    the switch is strict ``>``, not ``>=``.
    """
    url = "https://example.com/WorkItems?" + "$filter=" + ("z" * 2962)
    assert len(url) == 3000
    method, result_url = maybe_batch("GET", url, threshold=3000)
    assert method == "GET"
    assert result_url == url
