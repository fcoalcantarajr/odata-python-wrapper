"""WorkItemRevisions Pydantic model — frozen+strict+extra=forbid (HR-4).

NOTE: ADO Analytics blocks ``$expand=Revisions`` on WorkItems (HR-14/gotcha 5).
Use the ``WorkItemRevisions`` entity set directly instead.
"""

from __future__ import annotations

from pydantic import Field

from ado_odata_async.entities._base import ODataEntity


class WorkItemRevisions(ODataEntity):
    """A single revision of a WorkItem at a point in time.

    Accessed via the ``WorkItemRevisions`` entity set (not via
    ``$expand=Revisions``, which is blocked per HR-14).
    """

    WorkItemId: int
    Revision: int = Field(ge=1)
    Title: str
    WorkItemType: str
    ChangedDate: str
    State: str
    AreaSK: int | None = None
    IterationSK: int | None = None
    Tags: str | None = None
    AssignedTo: str | None = None
    Reason: str | None = None
