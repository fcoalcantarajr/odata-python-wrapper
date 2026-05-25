"""Canonical OData query option serialization per HR-9.

Serializes a dict of query options into a URL query string with
options ordered canonically: ``$apply → $filter → $orderby → $expand
→ $select → $skip → $top``.

Non-canonical options are appended after the canonical ones in the
order they were provided.
"""

from __future__ import annotations

from collections.abc import Mapping
from urllib.parse import quote

CANONICAL_ORDER: list[str] = [
    "$apply",
    "$filter",
    "$orderby",
    "$expand",
    "$select",
    "$skip",
    "$top",
]


class _HrError(ValueError):
    """Raised when a HARD RULE is violated at serialization time."""


def serialize(query: Mapping[str, str | None]) -> str:
    """Serialize a query options dict to a URL-encoded query string.

    Parameters
    ----------
    query:
        Mapping of OData query option names to their string values.
        ``None`` and ``""`` values are omitted.

    Returns
    -------
    str
        URL-encoded query string with options in canonical order
        (HR-9), or ``""`` if the input dict is empty.

    Raises
    ------
    _HrError
        If a HARD RULE is violated (e.g. $expand=Revisions per HR-14).
    """
    # Filter out None and empty-string values
    filtered: dict[str, str] = {k: v for k, v in query.items() if v is not None and v != ""}

    if not filtered:
        return ""

    # HR-14: $expand=Revisions is blocked (gotcha 5)
    expand_val = query.get("$expand")
    if expand_val:
        for segment in expand_val.split(","):
            base = segment.strip().split("(")[0].strip()
            if base == "Revisions":
                msg = "$expand=Revisions is blocked per HR-14 — use WorkItemRevisions instead"
                raise _HrError(msg)

    # Separate canonical and non-canonical keys
    canonical: list[tuple[str, str]] = []
    non_canonical: list[tuple[str, str]] = []

    for key, value in filtered.items():
        if key in CANONICAL_ORDER:
            canonical.append((key, value))
        else:
            non_canonical.append((key, value))

    # Sort canonical by their position in CANONICAL_ORDER
    canonical.sort(key=lambda item: CANONICAL_ORDER.index(item[0]))

    # Non-canonical stay in input order (Python 3.7+ dict insertion order)
    ordered_items = canonical + non_canonical

    # URL-encode values with quote (not quote_plus — use %20, not +)
    parts = [f"{key}={quote(value, safe='')}" for key, value in ordered_items]

    return "&".join(parts)
