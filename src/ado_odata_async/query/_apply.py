"""OData $apply expression tree builder.

Provides a fluent ``Apply`` class that constructs OData ``$apply``
expressions with ``groupby``, ``filter``, and ``aggregate`` support::

    >>> Apply.groupby("State").build()
    "$apply=groupby((State))"
    >>> Apply.groupby(["State","Priority"]).aggregate("Count","sum").build()
    "$apply=groupby((State,Priority))/aggregate(Count with sum as Count)"
    >>> Apply.filter(Filter.eq("State","Active")).build()
    "$apply=filter(State eq 'Active')"
"""

from __future__ import annotations

from ado_odata_async.query._filter import Filter


class Apply:
    """A fluent builder for OData ``$apply`` expressions.

    Constructed via class-method shortcuts or directly::

        Apply.groupby("State").build()
        Apply.filter(Filter.eq("A", "1")).build()
        Apply.aggregate("Effort", "sum").build()

    Or via direct constructor for entity-type enforcement (HR-13)::

        Apply(entity_type="WorkItemSnapshot").validate()

    Parameters
    ----------
    entity_type:
        Optional entity type name. When set to a Snapshot entity
        (e.g. ``"WorkItemSnapshot"``), ``validate()`` enforces that a
        required ``groupby(DateSK)`` or ``groupby(DateValue)`` is
        present (gotcha 4 / HR-13).
    """

    __slots__ = ("_aggregations", "_entity_type", "_filter_expr", "_groupby_fields")

    def __init__(self, entity_type: str | None = None) -> None:
        self._groupby_fields: list[str] = []
        self._filter_expr: Filter | None = None
        self._aggregations: list[tuple[str, str]] = []
        self._entity_type = entity_type

    # ------------------------------------------------------------------
    # Dual-role methods: class-level shortcut AND instance mutator
    # ------------------------------------------------------------------
    # When called on the class (e.g. Apply.groupby("State")), Python
    # passes the first positional argument as ``self`` (the field value)
    # and no ``*args``.  When called on an instance
    # (e.g. instance.groupby("State")), ``self`` is the instance and
    # the field value arrives via ``*args``.
    #
    # We detect the calling context with ``isinstance(self, Apply)``.

    def groupby(self, /, *args: str | list[str]) -> Apply:
        """Add / create a groupby clause.

        ``Apply.groupby(fields)``  — class shortcut, returns new Apply.
        ``instance.groupby(fields)`` — mutates and returns self.
        """
        if isinstance(self, Apply):
            # Instance path: args contains all positional arguments
            if len(args) == 1 and isinstance(args[0], list | tuple):
                # Single list/tuple argument
                self._groupby_fields = list(args[0])
            else:
                # Multiple string arguments
                self._groupby_fields = [arg for arg in args if isinstance(arg, str)]
            return self
        # Class-level shortcut: self is the first argument (fields)
        instance = Apply()  # type: ignore[unreachable]  # reason: intentional dual-role — self is fields at class level
        if isinstance(self, str):
            instance._groupby_fields = [self]
        else:
            instance._groupby_fields = list(self)
        return instance

    def filter(self, /, *args: Filter) -> Apply:
        """Add / create a filter clause.

        ``Apply.filter(expr)``  — class shortcut, returns new Apply.
        ``instance.filter(expr)`` — mutates and returns self.
        """
        if isinstance(self, Apply):
            self._filter_expr = args[0]
            return self
        instance = Apply()  # type: ignore[unreachable]  # reason: intentional dual-role — self is filter_expr at class level
        instance._filter_expr = self
        return instance

    def aggregate(self, /, *args: str) -> Apply:
        """Add / create an aggregate clause.

        ``Apply.aggregate(field, method)``  — class shortcut, returns new
        Apply.  ``instance.aggregate(field, method)`` — mutates and
        returns self.
        """
        if isinstance(self, Apply):
            field = args[0]
            method = args[1]
            self._aggregations.append((field, method))
            return self
        instance = Apply()  # type: ignore[unreachable]  # reason: intentional dual-role — self is field at class level
        instance._aggregations.append((self, args[0]))
        return instance

    # ------------------------------------------------------------------
    # Validation  (HR-13 / gotcha 4)
    # ------------------------------------------------------------------

    def validate(self) -> None:
        """Validate the ``$apply`` expression against HARD RULES.

        Raises
        ------
        ValueError
            If ``entity_type`` is ``"WorkItemSnapshot"`` and no
            ``groupby(DateSK)`` is present, or if ``entity_type``
            is ``"WorkItemBoardSnapshot"`` and no
            ``groupby(DateValue)`` is present (HR-13 / gotcha 4).
        """
        if self._entity_type == "WorkItemSnapshot" and "DateSK" not in self._groupby_fields:
            msg = f"{self._entity_type} requires groupby(DateSK)"
            raise ValueError(msg)

        if self._entity_type == "WorkItemBoardSnapshot" and "DateValue" not in self._groupby_fields:
            msg = f"{self._entity_type} requires groupby(DateValue)"
            raise ValueError(msg)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def build(self) -> str:
        """Serialize the ``$apply`` expression to an OData query string.

        Returns
        -------
        str
            The full ``$apply=...`` query string, e.g.
            ``"$apply=groupby((State))/aggregate(Count with sum)"``.
        """
        parts: list[str] = []

        if self._groupby_fields:
            inner = ",".join(self._groupby_fields)
            parts.append(f"groupby(({inner}))")

        if self._filter_expr is not None:
            parts.append(f"filter({self._filter_expr.build()})")

        if self._aggregations:
            agg_parts = [
                f"{field} with {method} as {field}" for field, method in self._aggregations
            ]
            parts.append(f"aggregate({', '.join(agg_parts)})")

        return f"$apply={'/'.join(parts)}"

    def __str__(self) -> str:
        """Return the same as ``build()`` — the full ``$apply=...`` string."""
        return self.build()
