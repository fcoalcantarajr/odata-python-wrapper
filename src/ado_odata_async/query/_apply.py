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

    def aggregate(self, /, *args: str, alias: str | None = None) -> Apply:
        """Add / create an aggregate clause.

        ``Apply.aggregate(field, method)``  — class shortcut, returns new
        Apply.  ``instance.aggregate(field, method)`` — mutates and
        returns self.

        For virtual field ``$count`` the *method* is used as the output
        alias (e.g. ``aggregate("$count", alias="Count")`` → ``$count as Count``).

        Raises
        ------
        NotImplementedError
            If *method* is ``"countdistinct"`` — this aggregator is
            blocked by ADO Analytics.
        """
        if isinstance(self, Apply):
            # Instance path: args contains all positional arguments
            if len(args) == 1:
                # $count with alias
                field = args[0]
                method = alias if alias is not None else field
            else:
                field = args[0]
                method = args[1]

            if method == "countdistinct":
                msg = (
                    "countdistinct is not supported by ADO Analytics. "
                    "Use '$count' inside groupby, or sum/min/max/avg on a numeric field. "
                    "See: https://learn.microsoft.com/en-us/azure/devops/report/extend-analytics/odata-query-guidelines?view=azure-devops"
                )
                raise NotImplementedError(msg)
            # Coalesce with previous aggregate if present
            if self._operations and self._operations[-1][0] == "aggregate":
                agg_list: list[tuple[str, str]] = self._operations[-1][1]
                agg_list.append((field, method))
            else:
                self._operations.append(("aggregate", [(field, method)]))
            return self
        # Class-level shortcut: self is the first argument (field)
        instance = Apply()  # type: ignore[unreachable]  # reason: intentional dual-role — self is field at class level
        field = self
        if args:
            method = args[0]
        elif alias is not None:
            method = alias
        else:
            msg = (
                "aggregate() requires a method argument, "
                "e.g. Apply.aggregate('field', 'sum') or "
                "Apply.aggregate('$count', alias='Count')"
            )
            raise ValueError(msg)
        if method == "countdistinct":
            msg = (
                "countdistinct is not supported by ADO Analytics. "
                "Use '$count' inside groupby, or sum/min/max/avg on a numeric field. "
                "See: https://learn.microsoft.com/en-us/azure/devops/report/extend-analytics/odata-query-guidelines?view=azure-devops"
            )
            raise NotImplementedError(msg)
        instance._operations.append(("aggregate", [(field, method)]))
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
        apply_value = self.build().removeprefix("$apply=")
        _check_snapshot_groupby(entity_set=self._entity_type or "", apply_value=apply_value)

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

        The pipeline preserves the declaration order of method calls.
        When an ``aggregate`` immediately follows a ``groupby`` the two are
        nested into a single clause::
            ``groupby((...),aggregate(...))``

        This matches the ADO Analytics syntax requirement (F12).
        """
        parts: list[str] = []
        i = 0
        while i < len(self._operations):
            op_name, payload = self._operations[i]

            if op_name == "groupby":
                inner = ",".join(payload)
                # F12: nest aggregate inside groupby when consecutive
                if i + 1 < len(self._operations) and self._operations[i + 1][0] == "aggregate":
                    agg_payload = self._operations[i + 1][1]
                    agg_parts = []
                    for field, method in agg_payload:
                        if field == "$count":
                            agg_parts.append(f"$count as {method}")
                        else:
                            agg_parts.append(f"{field} with {method} as {field}")
                    parts.append(f"groupby(({inner}),aggregate({', '.join(agg_parts)}))")
                    i += 1  # Skip the consumed aggregate
                else:
                    parts.append(f"groupby(({inner}))")
            elif op_name == "filter":
                parts.append(f"filter({payload.build()})")
            elif op_name == "aggregate":
                agg_parts = []
                for field, method in payload:
                    if field == "$count":
                        agg_parts.append(f"$count as {method}")
                    else:
                        agg_parts.append(f"{field} with {method} as {field}")
                parts.append(f"aggregate({', '.join(agg_parts)})")

            i += 1

        return f"$apply={'/'.join(parts)}"

    def __str__(self) -> str:
        """Return the same as ``build()`` — the full ``$apply=...`` string."""
        return self.build()


def _check_snapshot_groupby(entity_set: str, apply_value: str) -> None:
    """Validate HR-13: Snapshot entity sets require groupby on DateSK/DateValue.

    Shared single-source-of-truth for HR-13 enforcement (SR-004).
    **Why code-enforced, not audit.sh**:
    Detecting Snapshot violations requires semantic analysis of the ``$apply``
    expression tree (i.e., is DateSK/DateValue present in the outermost groupby?).
    Bash regex cannot reliably distinguish this without full OData parsing, as
    nested or chained operations can obscure the groupby field. Runtime validation
    here (at query serialization time) is sufficient and robust: violations fail
    immediately with a descriptive error, preventing silent bugs at the API level.
    Parameters
    ----------
    entity_set:
        Entity set name (e.g. ``"WorkItemSnapshot"``).
    apply_value:
        Serialized ``$apply`` value WITHOUT the ``$apply=`` prefix
        (e.g. ``"groupby((DateSK))"``).

    Raises
    ------
    ValueError
        If *entity_set* is a snapshot type and *apply_value* lacks the
        required ``groupby`` field.
    """
    required: str | None = {"WorkItemSnapshot": "DateSK", "WorkItemBoardSnapshot": "DateValue"}.get(
        entity_set
    )
    if required is None:
        return

    import re

    m = re.search(r"groupby\(\(([^)]+)\)\)", apply_value)
    if m:
        fields = [f.strip() for f in m.group(1).split(",")]
        if required in fields:
            return

    raise ValueError(f"{entity_set} requires groupby({required})")
