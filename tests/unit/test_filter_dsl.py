"""RED-phase tests for SPEC-005 Filter DSL builder — pure expression tree.

All 10 tests MUST fail (RED) because `ado_odata_async.query._filter.Filter`
does not exist yet. The import itself will raise `ImportError`.

No async, no aiohttp, no fixtures needed — these are pure sync string
assertions against `Filter.build()`.

Each test maps to one AC from specs/005-filter-dsl.md:
  - AC-1: eq with string value → "Field eq 'value'"
  - AC-2: single quote escaped (HR-12 gotcha 6)
  - AC-3: and_ combination with parentheses
  - AC-4: or_ combination with parentheses
  - AC-5: not_ negation
  - AC-6: contains function OData
  - AC-7: datetime ISO 8601 without datetime' prefix (HR-11 gotcha 7)
  - AC-8: null handling — eq None → "Field eq null"
  - AC-9: nested and/or precedence preservation
  - AC-10: ne comparator
"""

from __future__ import annotations

from ado_odata_async.query._filter import Filter


def test_ac1_eq_string_value() -> None:
    """AC-1: Filter.eq("Title", "Bug").build() → "Title eq 'Bug'".

    Asserts:
      - build() returns "Title eq 'Bug'"
    """
    result = Filter.eq("Title", "Bug").build()
    assert result == "Title eq 'Bug'"


def test_ac2_single_quote_escaping() -> None:
    """AC-2: Single quote in string value is escaped (HR-12 gotcha 6).

    Filter.eq("AssignedTo/UserName", "O'Keefe").build()
      → "AssignedTo/UserName eq 'O''Keefe'"
    And does NOT contain unescaped "O'Keefe".

    Asserts:
      - build() contains "AssignedTo/UserName eq 'O''Keefe'"
      - build() does NOT contain "O'Keefe" (unescaped)
    """
    result = Filter.eq("AssignedTo/UserName", "O'Keefe").build()
    assert "AssignedTo/UserName eq 'O''Keefe'" in result
    assert "O'Keefe" not in result.replace("''", "")


def test_ac3_and_combination() -> None:
    """AC-3: Filter.and_ combines two filters with parentheses.

    Filter.and_(Filter.eq("State", "Active"), Filter.eq("Priority", "1")).build()
      → "(State eq 'Active' and Priority eq '1')"

    Asserts:
      - build() returns "(State eq 'Active' and Priority eq '1')"
    """
    result = Filter.and_(
        Filter.eq("State", "Active"),
        Filter.eq("Priority", "1"),
    ).build()
    assert result == "(State eq 'Active' and Priority eq '1')"


def test_ac4_or_combination() -> None:
    """AC-4: Filter.or_ combines with parentheses.

    Filter.or_(Filter.eq("A", "1"), Filter.eq("B", "2")).build()
      → "(A eq '1' or B eq '2')"

    Asserts:
      - build() returns "(A eq '1' or B eq '2')"
    """
    result = Filter.or_(
        Filter.eq("A", "1"),
        Filter.eq("B", "2"),
    ).build()
    assert result == "(A eq '1' or B eq '2')"


def test_ac5_not_negation() -> None:
    """AC-5: Filter.not_ produces negation with parentheses.

    Filter.not_(Filter.eq("State", "Closed")).build()
      → "not (State eq 'Closed')"

    Asserts:
      - build() returns "not (State eq 'Closed')"
    """
    result = Filter.not_(Filter.eq("State", "Closed")).build()
    assert result == "not (State eq 'Closed')"


def test_ac6_contains_function() -> None:
    """AC-6: contains generates OData function.

    Filter.contains("Title", "security").build()
      → "contains(Title, 'security')"
    And format is contains(FieldName, 'value') without extra parens.

    Asserts:
      - build() returns "contains(Title, 'security')"
      - result matches contains(FieldName, 'value') pattern
    """
    result = Filter.contains("Title", "security").build()
    assert result == "contains(Title, 'security')"


def test_ac7_datetime_no_prefix() -> None:
    """AC-7: Datetime ISO 8601 without datetime' prefix (HR-11 gotcha 7).

    Filter.gt("ChangedDate", "2025-01-15T00:00:00Z").build()
      → "ChangedDate gt 2025-01-15T00:00:00Z"
    And does NOT contain "datetime'".

    Asserts:
      - build() returns "ChangedDate gt 2025-01-15T00:00:00Z"
      - build() does NOT contain "datetime'"
    """
    result = Filter.gt("ChangedDate", "2025-01-15T00:00:00Z").build()
    assert result == "ChangedDate gt 2025-01-15T00:00:00Z"
    assert "datetime'" not in result


def test_ac8_null_handling() -> None:
    """AC-8: eq with None produces "Field eq null".

    Filter.eq("AssignedTo", None).build() → "AssignedTo eq null"

    Asserts:
      - build() returns "AssignedTo eq null"
    """
    result = Filter.eq("AssignedTo", None).build()
    assert result == "AssignedTo eq null"


def test_ac9_nested_and_or_precedence() -> None:
    """AC-9: Nested and/or preserves precedence with parentheses.

    Filter.or_(
      Filter.and_(Filter.eq("A", "1"), Filter.eq("B", "2")),
      Filter.eq("C", "3"),
    ).build()
      → "((A eq '1' and B eq '2') or C eq '3')"

    Asserts:
      - build() returns "((A eq '1' and B eq '2') or C eq '3')"
    """
    result = Filter.or_(
        Filter.and_(
            Filter.eq("A", "1"),
            Filter.eq("B", "2"),
        ),
        Filter.eq("C", "3"),
    ).build()
    assert result == "((A eq '1' and B eq '2') or C eq '3')"


def test_ac10_ne_comparator() -> None:
    """AC-10: ne (not equal) comparator.

    Filter.ne("State", "Deleted").build() → "State ne 'Deleted'"

    Asserts:
      - build() returns "State ne 'Deleted'"
    """
    result = Filter.ne("State", "Deleted").build()
    assert result == "State ne 'Deleted'"
