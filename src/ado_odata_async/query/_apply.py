"""OData $apply expression tree builder.

Provides a fluent ``Apply`` class that constructs OData ``$apply``
expressions with ``groupby``, ``filter``, and ``aggregate`` support::

    >>> Apply.groupby("State").build()
    "$apply=groupby((State))"
    >>> Apply.groupby(["State","Priority"]).aggregate("Effort","sum").build()
    "$apply=groupby((State,Priority))/aggregate(Effort with sum as Effort)"
    >>> Apply.filter(Filter.eq("State","Active")).build()
    "$apply=filter(State eq 'Active')"
"""

from __future__ import annotations

from typing import Any

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

    __slots__ = ("_entity_type", "_operations")

    def __init__(self, entity_type: str | None = None) -> None:
        self._operations: list[tuple[str, Any]] = []
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
            fields: list[str]
            if len(args) == 1 and isinstance(args[0], list | tuple):
                fields = list(args[0])
            else:
                fields = [arg for arg in args if isinstance(arg, str)]
            if not fields:
                msg = "groupby() requires at least one field"
                raise ValueError(msg)
            # Replace existing groupby if present (groupby is idempotent)
            for i, (op_name, _) in enumerate(self._operations):
                if op_name == "groupby":
                    self._operations[i] = ("groupby", fields)
                    return self
            self._operations.append(("groupby", fields))
            return self
        # Class-level shortcut: self is the first argument (fields)
        instance = Apply()  # type: ignore[unreachable]  # reason: intentional dual-role — self is fields at class level
        if isinstance(self, str):
            # Forward *args to support Apply.groupby("A", "B", "C")
            fields = [self]
            fields.extend(arg for arg in args if isinstance(arg, str))
            instance._operations.append(("groupby", fields))
        else:
            instance._operations.append(("groupby", list(self)))
        return instance

    def filter(self, /, *args: Filter) -> Apply:
        """Add / create a filter clause.

        ``Apply.filter(expr)``  — class shortcut, returns new Apply.
        ``instance.filter(expr)`` — mutates and returns self.
        """
        if isinstance(self, Apply):
            self._operations.append(("filter", args[0]))
            return self
        instance = Apply()  # type: ignore[unreachable]  # reason: intentional dual-role — self is filter_expr at class level
        instance._operations.append(("filter", self))
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
            # Coalesce with previous aggregate if present
            if self._operations and self._operations[-1][0] == "aggregate":
                agg_list: list[tuple[str, str]] = self._operations[-1][1]
                agg_list.append((field, method))
            else:
                self._operations.append(("aggregate", [(field, method)]))
            return self
        instance = Apply()  # type: ignore[unreachable]  # reason: intentional dual-role — self is field at class level
        instance._operations.append(("aggregate", [(self, args[0])]))
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
        groupby_fields: list[str] = []
        for op_name, payload in self._operations:
            if op_name == "groupby":
                groupby_fields = payload
                break

        if self._entity_type == "WorkItemSnapshot" and "DateSK" not in groupby_fields:
            msg = f"{self._entity_type} requires groupby(DateSK)"
            raise ValueError(msg)

        if self._entity_type == "WorkItemBoardSnapshot" and "DateValue" not in groupby_fields:
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
            ``"$apply=groupby((State))/aggregate(Effort with sum as Effort)"``.

        The pipeline preserves the declaration order of method calls:
        ``filter()`` then ``groupby()`` then ``aggregate()`` produces
        ``$apply=filter(...)/groupby(...)/aggregate(...)``.
        """
        parts: list[str] = []

        for op_name, payload in self._operations:
            if op_name == "groupby":
                inner = ",".join(payload)
                parts.append(f"groupby(({inner}))")
            elif op_name == "filter":
                parts.append(f"filter({payload.build()})")
            elif op_name == "aggregate":
                agg_parts = [
                    f"{field} with {method} as {field}" for field, method in payload
                ]
                parts.append(f"aggregate({', '.join(agg_parts)})")

        return f"$apply={'/'.join(parts)}"

    def __str__(self) -> str:
        """Return the same as ``build()`` — the full ``$apply=...`` string."""
        return self.build()
