"""OData $filter expression tree builder.

Provides a composable Filter class that constructs OData $filter
expressions with proper escaping, type handling, and operator support.

Usage::

    >>> from ado_odata_async.query._filter import Filter
    >>> Filter.eq("Title", "Bug").build()
    "Title eq 'Bug'"
    >>> Filter.and_(Filter.eq("A", "1"), Filter.eq("B", "2")).build()
    "(A eq '1' and B eq '2')"
"""

from __future__ import annotations

import re
from enum import Enum

_ISO_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T")

_Value = str | int | float | bool | None


class _NodeKind(Enum):
    COMPARISON = "comparison"
    AND = "and"
    OR = "or"
    NOT = "not"
    CONTAINS = "contains"


class Filter:
    """A node in an OData $filter expression tree.

    Constructed via static factory methods — users never instantiate
    ``Filter`` directly::

        Filter.eq(field, value)       # comparison (eq)
        Filter.ne(field, value)       # comparison (ne)
        Filter.gt(field, value)       # comparison (gt)
        Filter.ge(field, value)       # comparison (ge)
        Filter.lt(field, value)       # comparison (lt)
        Filter.le(field, value)       # comparison (le)
        Filter.and_(*filters)         # logical AND
        Filter.or_(*filters)          # logical OR
        Filter.not_(filter)           # logical NOT
        Filter.contains(field, value) # contains function

    Call ``.build()`` to get the OData ``$filter`` string.
    """

    __slots__ = ("_children", "_field", "_kind", "_operator", "_value")

    def __init__(
        self,
        kind: _NodeKind,
        field: str = "",
        operator: str = "",
        value: _Value = None,
        children: list[Filter] | None = None,
    ) -> None:
        self._kind = kind
        self._field = field
        self._operator = operator
        self._value = value
        self._children = children if children is not None else []

    # ------------------------------------------------------------------
    # Value serialization helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_value(value: _Value) -> str:
        """Serialize a Python value to its OData literal representation.

        Rules:
            ``None`` → ``"null"``
            ``bool`` → ``"true"`` / ``"false"`` (lowercase)
            ``int`` / ``float`` → plain ``str(value)``
            ``str`` → single-quoted with internal quotes doubled (HR-12),
                      except ISO-8601 datetime strings which are emitted
                      bare (HR-11).
        """
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, int | float):
            return str(value)
        if isinstance(value, str):
            if _ISO_DATETIME_RE.match(value):
                return value
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        # All _Value branches covered above; fallback for completeness.
        return str(value)  # type: ignore[unreachable]  # reason: safety fallback

    # ------------------------------------------------------------------
    # Factory methods: comparison operators
    # ------------------------------------------------------------------

    @staticmethod
    def eq(field: str, value: _Value = None) -> Filter:
        """``Field eq value``."""
        return Filter(_NodeKind.COMPARISON, field=field, operator="eq", value=value)

    @staticmethod
    def ne(field: str, value: _Value = None) -> Filter:
        """``Field ne value``."""
        return Filter(_NodeKind.COMPARISON, field=field, operator="ne", value=value)

    @staticmethod
    def gt(field: str, value: _Value = None) -> Filter:
        """``Field gt value``."""
        return Filter(_NodeKind.COMPARISON, field=field, operator="gt", value=value)

    @staticmethod
    def ge(field: str, value: _Value = None) -> Filter:
        """``Field ge value``."""
        return Filter(_NodeKind.COMPARISON, field=field, operator="ge", value=value)

    @staticmethod
    def lt(field: str, value: _Value = None) -> Filter:
        """``Field lt value``."""
        return Filter(_NodeKind.COMPARISON, field=field, operator="lt", value=value)

    @staticmethod
    def le(field: str, value: _Value = None) -> Filter:
        """``Field le value``."""
        return Filter(_NodeKind.COMPARISON, field=field, operator="le", value=value)

    # ------------------------------------------------------------------
    # Factory methods: logical combinators
    # ------------------------------------------------------------------

    @staticmethod
    def and_(*filters: Filter) -> Filter:
        """Logical AND — wraps children in ``(  )``."""
        return Filter(_NodeKind.AND, children=list(filters))

    @staticmethod
    def or_(*filters: Filter) -> Filter:
        """Logical OR — wraps children in ``(  )``."""
        return Filter(_NodeKind.OR, children=list(filters))

    @staticmethod
    def not_(filter_node: Filter) -> Filter:
        """Logical NOT — emits ``not (child)``."""
        return Filter(_NodeKind.NOT, children=[filter_node])

    # ------------------------------------------------------------------
    # Factory methods: OData functions
    # ------------------------------------------------------------------

    @staticmethod
    def contains(field: str, value: _Value = None) -> Filter:
        """``contains(field, value)`` OData function."""
        return Filter(_NodeKind.CONTAINS, field=field, value=value)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def build(self) -> str:
        """Walk the expression tree and return the OData ``$filter`` string."""
        kind = self._kind

        if kind is _NodeKind.COMPARISON:
            return f"{self._field} {self._operator} {self._format_value(self._value)}"

        if kind is _NodeKind.AND:
            inner = " and ".join(c.build() for c in self._children)
            return f"({inner})"

        if kind is _NodeKind.OR:
            inner = " or ".join(c.build() for c in self._children)
            return f"({inner})"

        if kind is _NodeKind.NOT:
            return f"not ({self._children[0].build()})"

        if kind is _NodeKind.CONTAINS:
            return f"contains({self._field}, {self._format_value(self._value)})"

        raise ValueError(f"Unknown node kind: {kind}")
