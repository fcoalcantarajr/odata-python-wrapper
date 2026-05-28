"""Tests for AS-001: _serialize.py:58 reads filtered dict, not raw query."""

from __future__ import annotations

import pytest

from ado_odata_async.query._serialize import _HrError, serialize


class TestSerializeExpandRevisions:
    """AS-001 AC-1 through AC-4: HR-14 validation reads from filtered dict."""

    def test_ac1_expand_revisions_with_none_filter_raises(self) -> None:
        """AC-1: $expand=Revisions with $filter=None is blocked.

        Given the serialize function receives {"$expand": "Revisions", "$filter": None}
        When serialize() is called
        Then _HrError is raised with message containing "$expand=Revisions is blocked"
        """
        with pytest.raises(_HrError, match="\\$expand=Revisions is blocked"):
            serialize({"$expand": "Revisions", "$filter": None})

    def test_ac2_expand_revisions_alone_raises(self) -> None:
        """AC-2: $expand=Revisions without $filter is still blocked.

        Given the serialize function receives {"$expand": "Revisions"}
        When serialize() is called
        Then _HrError is raised with message containing "$expand=Revisions is blocked"
        """
        with pytest.raises(_HrError, match="\\$expand=Revisions is blocked"):
            serialize({"$expand": "Revisions"})

    def test_ac3_nonblocked_expand_passes(self) -> None:
        """AC-3: Non-blocked expand passes through.

        Given the serialize function receives
        {"$expand": "Children", "$filter": "State eq 'Active'"}
        When serialize() is called
        Then the returned string contains "$expand=Children"
          And the returned string contains "$filter=State%20eq%20%27Active%27"
        """
        result = serialize({"$expand": "Children", "$filter": "State eq 'Active'"})
        assert "$expand=Children" in result
        assert "$filter=State%20eq%20%27Active%27" in result

    def test_ac4_all_none_empty_returns_empty(self) -> None:
        """AC-4: Empty filtered dict returns empty string.

        Given the serialize function receives {"$expand": None, "$filter": ""}
        When serialize() is called
        Then the returned string is "" (empty)
        """
        result = serialize({"$expand": None, "$filter": ""})
        assert result == ""
