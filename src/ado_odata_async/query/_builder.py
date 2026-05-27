"""Immutable chainable QueryBuilder for OData queries (SPEC-011).

Usage::

    b = client.query("WorkItems").select("Title", "State").top(10)
    data = await b.get()
    async for page in b.paginate():
        ...
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from copy import deepcopy
from typing import TYPE_CHECKING, Any

from ado_odata_async.query._serialize import serialize

if TYPE_CHECKING:
    from ado_odata_async.client import AdoODataClient
    from ado_odata_async.query._apply import Apply
    from ado_odata_async.query._filter import Filter

logger = logging.getLogger(__name__)


class QueryBuilder:
    """Immutable builder for OData queries.

    Each setter returns a new QueryBuilder instance with the option
    added/updated, leaving the original unchanged (AC-5).
    """

    def __init__(
        self,
        client: AdoODataClient | None = None,
        entity_set: str = "",
    ) -> None:
        self._client = client
        self._entity_set = entity_set
        self._options: dict[str, str] = {}

    # ── internal helpers ────────────────────────────────────

    def _copy(self) -> QueryBuilder:
        """Return a shallow copy with deep-copied options."""
        new = QueryBuilder(self._client, self._entity_set)
        new._options = deepcopy(self._options)
        return new

    def _query_dict(self) -> dict[str, str]:
        """Return the current options dict for client.get/paginate."""
        return dict(self._options)

    # ── string representations ──────────────────────────────

    def __str__(self) -> str:
        """OData query string with canonical ordering per HR-9."""
        return serialize(self._options)

    def __repr__(self) -> str:
        """Debug representation exposing entity set and active clauses."""
        clauses = ", ".join(f"{k}={v!r}" for k, v in self._options.items())
        entity = self._entity_set or "(none)"
        return f"{type(self).__name__}(entity_set={entity!r}, clauses=[{clauses}])"

    # ── chainable setters (all return new QueryBuilder) ─────

    def apply(self, a: Apply) -> QueryBuilder:
        """Add ``$apply`` clause."""
        from ado_odata_async.query._apply import _check_snapshot_groupby

        b = self._copy()
        value = a.build()
        if value.startswith("$apply="):
            value = value[len("$apply=") :]
        _check_snapshot_groupby(entity_set=self._entity_set, apply_value=value)
        b._options["$apply"] = value
        return b

    def filter(self, f: Filter) -> QueryBuilder:
        """Add ``$filter`` clause."""
        b = self._copy()
        b._options["$filter"] = f.build()
        return b

    def orderby(self, *fields: str) -> QueryBuilder:
        """Add ``$orderby`` clause (comma-separated fields)."""
        b = self._copy()
        b._options["$orderby"] = ",".join(fields)
        return b

    def expand(self, *rels: str) -> QueryBuilder:
        """Add ``$expand`` clause (comma-separated relations)."""
        b = self._copy()
        b._options["$expand"] = ",".join(rels)
        return b

    def select(self, *fields: str | list[str]) -> QueryBuilder:
        """Add ``$select`` clause (comma-separated fields)."""
        b = self._copy()
        if len(fields) == 1 and isinstance(fields[0], list | tuple):
            b._options["$select"] = ",".join(str(x) for x in fields[0])
        else:
            normalized: list[str] = [str(f) for f in fields]
            b._options["$select"] = ",".join(normalized)
        return b

    def skip(self, n: int) -> QueryBuilder:
        """Add ``$skip`` clause."""
        b = self._copy()
        b._options["$skip"] = str(n)
        return b

    def top(self, n: int) -> QueryBuilder:
        """Add ``$top`` clause."""
        b = self._copy()
        b._options["$top"] = str(n)
        return b

    # ── HR-13 enforcement (snapshot entity sets) ─────────────

    def _validate_hr13(self) -> None:
        """Raise ``ValueError`` if a snapshot entity set lacks required ``groupby``."""
        from ado_odata_async.query._apply import _check_snapshot_groupby

        apply_val = self._options.get("$apply", "")
        _check_snapshot_groupby(entity_set=self._entity_set, apply_value=apply_val)

    # ── terminal operations ─────────────────────────────────

    async def get(self) -> dict[str, Any]:
        """Execute the query and return the response dict.

        Raises:
            RuntimeError: If builder has no client or entity set.
            ValueError: If snapshot entity set lacks required groupby (HR-13).
        """
        if self._client is None or not self._entity_set:
            raise RuntimeError("QueryBuilder requires client and entity_set to execute")
        self._validate_hr13()
        result = await self._client.get(self._entity_set, **self._query_dict())
        return result

    def paginate(self, *, top: int = 100) -> AsyncIterator[dict[str, Any]]:
        """Paginate over results, yielding each page dict.

        Args:
            top: Page size (``$top``). Must be >= 1.

        Raises:
            RuntimeError: If builder has no client or entity set.
            ValueError: If *top* < 1 or snapshot entity set lacks groupby (HR-13).
        """
        if self._client is None or not self._entity_set:
            raise RuntimeError("QueryBuilder requires client and entity_set to paginate")
        if top < 1:
            raise ValueError("top must be >= 1")
        self._validate_hr13()
        return self._client.paginate(self._entity_set, top=top, query=self._query_dict())
