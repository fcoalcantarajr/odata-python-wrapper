"""Entity models (Pydantic frozen + strict). One module per entity set."""

from __future__ import annotations

from ado_odata_async.entities._board import (
    WorkItemBoardSnapshot,
    WorkItemBoardSnapshotWithDescription,
)
from ado_odata_async.entities._reference import Area, Iteration, Project, Team
from ado_odata_async.entities._system import Date, User, WorkItemLink, WorkItemType
from ado_odata_async.entities._workitem import WorkItem
from ado_odata_async.entities._workitemrevisions import WorkItemRevisions

__all__: list[str] = [
    "Area",
    "Date",
    "Iteration",
    "Project",
    "Team",
    "User",
    "WorkItem",
    "WorkItemBoardSnapshot",
    "WorkItemBoardSnapshotWithDescription",
    "WorkItemLink",
    "WorkItemRevisions",
    "WorkItemType",
]
