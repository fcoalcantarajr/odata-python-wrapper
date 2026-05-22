"""RED-phase tests for SPEC-007 query option serialization order per HR-9.

All 5 tests MUST fail (RED) because `ado_odata_async.query._serialize.serialize`
does not exist yet. The import itself will raise ``ImportError``.

Pure sync tests — no async, no fixtures needed.

Each test maps to one AC from specs/007-serialization-order.md:
  - AC-1: canonical order respected ($apply before $filter before $top)
  - AC-2: full 7-option canonical order
  - AC-3: None/empty values omitted
  - AC-4: unknown options appended at end
  - AC-5: empty dict returns empty string
"""

from __future__ import annotations

import re

from ado_odata_async.query._serialize import serialize


def test_ac1_canonical_order_respected() -> None:
    """AC-1: Canonical order is respected regardless of dict insertion order.

    serialize({"$filter": "x eq 1", "$top": "10", "$apply": "groupby((y))"})
      → result matches pattern \\$apply=...&\\$filter=...&\\$top=...

    Confirms ``$apply`` appears before ``$filter`` which appears before
    ``$top`` in the serialized output, even though the dict was given
    in a different order.
    """
    result = serialize({"$filter": "x eq 1", "$top": "10", "$apply": "groupby((y))"})
    assert re.search(
        r"\$apply=.*&\$filter=.*&\$top=.*",
        result,
    )


def test_ac2_full_order() -> None:
    """AC-2: All 7 canonical options appear in exact canonical order.

    serialize() with all 7 options:
      ``$apply → $filter → $orderby → $expand → $select → $skip → $top``

    The dict keys are intentionally passed in reverse order to verify the
    ordering is enforced by ``serialize()``, not inherited from dict ordering.
    """
    result = serialize(
        {
            "$top": "50",
            "$skip": "10",
            "$select": "WorkItemId,Title",
            "$expand": "Children",
            "$orderby": "WorkItemId asc",
            "$filter": "State eq 'Active'",
            "$apply": "groupby((Priority))",
        }
    )
    expected_order = (
        r"\$apply=.*&"
        r"\$filter=.*&"
        r"\$orderby=.*&"
        r"\$expand=.*&"
        r"\$select=.*&"
        r"\$skip=.*&"
        r"\$top=50$"
    )
    assert re.search(expected_order, result)


def test_ac3_none_empty_omitted() -> None:
    """AC-3: ``None`` and ``""`` values are filtered out.

    serialize({"$filter": "x eq 1", "$top": None, "$skip": ""})
      → ``"$filter=x%20eq%201"``

    ``None`` and empty-string values must be removed entirely — not
    serialized as ``$top=None`` or ``$skip=``.
    """
    result = serialize({"$filter": "x eq 1", "$top": None, "$skip": ""})
    assert result == "$filter=x%20eq%201"


def test_ac4_unknown_options_appended() -> None:
    """AC-4: Non-canonical options appear after all canonical ones.

    serialize({"$filter": "x eq 1", "$custom": "val"})
      → result ends with ``"$custom=val"``

    Any option not in the canonical set (``$apply``, ``$filter``,
    ``$orderby``, ``$expand``, ``$select``, ``$skip``, ``$top``)
    should be appended after all canonical options, in the order
    they were provided in the dict.
    """
    result = serialize({"$filter": "x eq 1", "$custom": "val"})
    assert result.endswith("$custom=val")
    assert result.index("$filter") < result.index("$custom")


def test_ac5_empty_dict() -> None:
    """AC-5: Empty dict returns empty string.

    serialize({}) → ``""``

    With no query options the serialized result is an empty string,
    allowing callers to safely concatenate it to a base URL.
    """
    result = serialize({})
    assert result == ""
