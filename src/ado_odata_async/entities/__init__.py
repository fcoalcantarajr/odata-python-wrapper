"""Entity models (Pydantic frozen + strict). One module per entity set."""

from __future__ import annotations

from ado_odata_async.entities._workitem import WorkItem

__all__: list[str] = [
    "WorkItem",
]
