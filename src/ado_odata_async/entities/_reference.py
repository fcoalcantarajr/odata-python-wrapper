"""Reference-data Pydantic models — simple, frozen+strict+extra=forbid (HR-4).

Iteration, Project, Team, and Area are dimension tables in the ADO
Analytics OData schema. All are read-only reference data.
"""

from __future__ import annotations

from ado_odata_async.entities._base import ODataEntity


class Iteration(ODataEntity):
    """ADO iteration (sprint)."""

    IterationSK: int
    Identifier: str
    IterationName: str
    StartDate: str | None = None
    EndDate: str | None = None


class Project(ODataEntity):
    """ADO project."""

    ProjectSK: int
    ProjectId: str
    ProjectName: str
    ProjectDescription: str | None = None


class Team(ODataEntity):
    """ADO team."""

    TeamSK: int
    TeamId: str
    TeamName: str
    TeamDescription: str | None = None


class Area(ODataEntity):
    """ADO area path."""

    AreaSK: int
    AreaId: str
    AreaPath: str
    AreaName: str
    AreaLevel1: str | None = None
    AreaLevel2: str | None = None
    AreaLevel3: str | None = None
    AreaLevel4: str | None = None
