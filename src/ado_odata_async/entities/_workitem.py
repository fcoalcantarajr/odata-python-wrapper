"""WorkItem Pydantic model — frozen+strict+extra=forbid per HR-4."""

from __future__ import annotations

import logging

from pydantic import Field, field_validator

from ado_odata_async.entities._base import ODataEntity

logger = logging.getLogger(__name__)

WORK_ITEM_TYPES: tuple[str, ...] = (
    "Bug",
    "User Story",
    "Task",
    "Feature",
    "Epic",
)


class WorkItem(ODataEntity):
    """ADO Analytics WorkItem entity.

    Fields based on OData $metadata for the WorkItem entity set.
    frozen+strict+extra=forbid inherited from ODataEntity (HR-4).
    WorkItemType accepts any string; non-standard types log a warning.
    """

    WorkItemId: int = Field(gt=0)
    Title: str
    WorkItemType: str

    @field_validator("WorkItemType")
    @classmethod
    def _validate_work_item_type(cls, v: str) -> str:
        if v not in WORK_ITEM_TYPES:
            logger.warning(
                "WorkItemType %r not in standard set %s",
                v,
                WORK_ITEM_TYPES,
            )
        return v
