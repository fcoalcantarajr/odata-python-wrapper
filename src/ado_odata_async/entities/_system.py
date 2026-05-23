"""System-level entity Pydantic models — dimension tables (HR-4).

Date (analytics date dimension), User, WorkItemType, and WorkItemLink
are system entity sets in the ADO Analytics OData schema.
"""

from __future__ import annotations

from pydantic import Field

from ado_odata_async.entities._base import ODataEntity


class Date(ODataEntity):
    """Analytics date dimension."""

    DateSK: int
    Date: str
    Day: int = Field(ge=1, le=31)
    Month: int = Field(ge=1, le=12)
    Year: int
    Quarter: int = Field(ge=1, le=4)
    DayOfWeek: int = Field(ge=0, le=6)
    MonthName: str
    DayOfWeekName: str
    WeekOfYear: int = Field(ge=1, le=53)


class User(ODataEntity):
    """Azure DevOps user/identity."""

    UserSK: int
    UserId: str
    UserName: str
    DisplayName: str | None = None


class WorkItemType(ODataEntity):
    """Work item type definition."""

    WorkItemTypeSK: int
    WorkItemTypeName: str
    WorkItemTypeDescription: str | None = None


class WorkItemLink(ODataEntity):
    """Link between two work items."""

    WorkItemLinkId: int
    SourceWorkItemId: int
    TargetWorkItemId: int
    LinkType: str
    LinkTypeReferenceName: str | None = None
