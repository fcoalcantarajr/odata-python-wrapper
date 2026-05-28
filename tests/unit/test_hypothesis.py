"""AS-006: Property-based tests with Hypothesis for Filter/Apply/Serialize."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from ado_odata_async.query._filter import Filter
from ado_odata_async.query._serialize import serialize


class TestFilterBuildProperties:
    """AC-1 through AC-2: Filter.build() properties."""

    @given(field=st.text(min_size=1, max_size=50), value=st.text(min_size=0, max_size=100))
    @settings(max_examples=50)
    def test_ac1_eq_never_crashes(self, field: str, value: str) -> None:
        """AC-1: Filter.eq() with any string never crashes."""
        result = Filter.eq(field, value).build()
        assert isinstance(result, str)
        assert field in result

    @given(values=st.lists(st.text(min_size=1, max_size=20), min_size=2, max_size=5))
    @settings(max_examples=30)
    def test_ac2_and_never_crashes(self, values: list[str]) -> None:
        """AC-2: Filter.and_() with 2+ items never crashes."""
        filters = [Filter.eq(f"field{i}", v) for i, v in enumerate(values)]
        result = Filter.and_(*filters).build()
        assert isinstance(result, str)
        assert "and" in result


class TestSerializeProperties:
    """AC-3 through AC-4: serialize() properties."""

    @given(
        data=st.dictionaries(
            keys=st.sampled_from(["$filter", "$select", "$top", "$orderby"]),
            values=st.text(min_size=1, max_size=50),
            min_size=0,
            max_size=4,
        )
    )
    @settings(max_examples=50)
    def test_ac3_serialize_never_crashes(self, data: dict[str, str]) -> None:
        """AC-3: serialize() with any valid dict never crashes."""
        result = serialize(data)
        assert isinstance(result, str)

    @given(
        expand=st.text(min_size=1, max_size=20).filter(lambda x: "Revisions" not in x),
        filter_val=st.text(min_size=1, max_size=50),
    )
    @settings(max_examples=30)
    def test_ac4_non_revisions_expand_always_passes(self, expand: str, filter_val: str) -> None:
        """AC-4: serialize() with non-Revisions expand always passes."""
        result = serialize({"$expand": expand, "$filter": filter_val})
        assert "$expand=" in result
