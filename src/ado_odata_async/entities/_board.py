"""Board snapshot Pydantic models — frozen+strict+extra=forbid (HR-4).

HR-13/gotcha 4: ``WorkItemBoardSnapshot`` and
``WorkItemBoardSnapshotWithDescription`` require ``$apply`` with
``groupby(DateValue)`` — enforced in the Apply DSL, not in this model.
"""

from __future__ import annotations

from pydantic import Field

from ado_odata_async.entities._base import ODataEntity


class WorkItemBoardSnapshot(ODataEntity):
    """Daily board snapshot per work item.

    HR-13: Requires ``$apply=groupby((DateValue))`` when querying.
    """

    WorkItemId: int
    BoardSK: int
    BoardName: str
    BoardColumnName: str
    BoardColumnOrder: int
    BoardRowName: str | None = None
    BoardRowOrder: int | None = None
    DateSK: int = Field(ge=20200101)
    State: str
    WorkItemType: str
    IsCurrent: bool


class WorkItemBoardSnapshotWithDescription(WorkItemBoardSnapshot):
    """Same as WorkItemBoardSnapshot but includes Description field.

    Description is a large text field — excluded from the base snapshot
    to save bandwidth by default.
    """

    Description: str | None = None
