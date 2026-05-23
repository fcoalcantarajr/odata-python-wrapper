"""Tests for SPEC-010 remaining entities — all tests MUST FAIL initially (RED phase).

Models don't exist yet in src/. All fail with ImportError before impl.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

# ── AC-1: WorkItemRevisions model ───────────────────────────


def test_ac1_work_item_revisions() -> None:
    """AC-1: WorkItemRevisions has Revision >= 1 and WorkItemId."""
    from ado_odata_async import (
        WorkItemRevisions,  # type: ignore[import-untyped]  # reason: RED phase
    )

    row = {
        "WorkItemId": 42,
        "Revision": 1,
        "Title": "Fix login bug",
        "WorkItemType": "Bug",
        "ChangedDate": "2020-01-01T00:00:00Z",
        "State": "Active",
    }
    instance = WorkItemRevisions.model_validate(row)
    assert instance.Revision == 1
    assert instance.WorkItemId == 42


def test_ac1_revision_zero_rejected() -> None:
    """AC-1: Revision=0 raises ValidationError."""
    from ado_odata_async import (
        WorkItemRevisions,  # type: ignore[import-untyped]  # reason: RED phase
    )

    row = {
        "WorkItemId": 42,
        "Revision": 0,
        "Title": "x",
        "WorkItemType": "Bug",
        "ChangedDate": "2020-01-01T00:00:00Z",
        "State": "Active",
    }
    with pytest.raises(ValidationError):
        WorkItemRevisions.model_validate(row)


# ── AC-2: WorkItemBoardSnapshot model ────────────────────────


def test_ac2_board_snapshot() -> None:
    """AC-2: WorkItemBoardSnapshot has DateSK as int."""
    from ado_odata_async import (
        WorkItemBoardSnapshot,  # type: ignore[import-untyped]  # reason: RED phase
    )

    row = {
        "WorkItemId": 1,
        "DateSK": 20260522,
        "BoardSK": 1,
        "BoardName": "Kanban",
        "BoardColumnName": "Doing",
        "BoardColumnOrder": 1,
        "State": "Active",
        "WorkItemType": "User Story",
        "IsCurrent": True,
    }
    instance = WorkItemBoardSnapshot.model_validate(row)
    assert instance.DateSK == 20260522
    assert isinstance(instance.DateSK, int)


# ── AC-3: Iteration model ───────────────────────────────────


def test_ac3_iteration() -> None:
    """AC-3: Iteration has Identifier as str (not None)."""
    from ado_odata_async import (
        Iteration,  # type: ignore[import-untyped]  # reason: RED phase
    )

    row = {
        "IterationSK": 1,
        "Identifier": "Project\\Sprint 1",
        "IterationName": "Sprint 1",
    }
    instance = Iteration.model_validate(row)
    assert isinstance(instance.Identifier, str)
    assert instance.Identifier is not None


def test_ac3_identifier_missing_rejected() -> None:
    """AC-3: Missing Identifier raises ValidationError."""
    from ado_odata_async import (
        Iteration,  # type: ignore[import-untyped]  # reason: RED phase
    )

    row = {"IterationSK": 1, "IterationName": "Sprint 1"}
    with pytest.raises(ValidationError):
        Iteration.model_validate(row)


# ── AC-4: Project model ─────────────────────────────────────


def test_ac4_project() -> None:
    """AC-4: Project has ProjectSK (int) and ProjectName (str)."""
    from ado_odata_async import (
        Project,  # type: ignore[import-untyped]  # reason: RED phase
    )

    row = {"ProjectSK": 1, "ProjectId": "guid-123", "ProjectName": "My Project"}
    instance = Project.model_validate(row)
    assert isinstance(instance.ProjectSK, int)
    assert isinstance(instance.ProjectName, str)
    assert instance.ProjectName == "My Project"


# ── AC-5: Team model ────────────────────────────────────────


def test_ac5_team() -> None:
    """AC-5: Team has TeamSK (int) and TeamName (str)."""
    from ado_odata_async import (
        Team,  # type: ignore[import-untyped]  # reason: RED phase
    )

    row = {"TeamSK": 1, "TeamId": "guid-456", "TeamName": "My Team"}
    instance = Team.model_validate(row)
    assert isinstance(instance.TeamSK, int)
    assert isinstance(instance.TeamName, str)


# ── AC-6: All models frozen+strict ──────────────────────────


def test_ac6_all_frozen_strict() -> None:
    """AC-6: All entity models have frozen+strict+extra='forbid'."""
    from ado_odata_async import (
        Area,
        Date,
        Iteration,
        Project,
        Team,
        User,
        WorkItemBoardSnapshot,
        WorkItemBoardSnapshotWithDescription,
        WorkItemLink,
        WorkItemRevisions,
        WorkItemType,
    )  # type: ignore[import-untyped]  # reason: RED phase

    models = [
        WorkItemRevisions,
        WorkItemBoardSnapshot,
        WorkItemBoardSnapshotWithDescription,
        Iteration,
        Project,
        Team,
        Area,
        Date,
        User,
        WorkItemType,
        WorkItemLink,
    ]
    for model in models:
        cfg = model.model_config
        assert cfg.get("frozen") is True, f"{model.__name__} not frozen"
        assert cfg.get("strict") is True, f"{model.__name__} not strict"
        assert cfg.get("extra") == "forbid", f"{model.__name__} not extra=forbid"


# ── AC-7: WorkItemBoardSnapshotWithDescription ──────────────


def test_ac7_board_snapshot_with_description() -> None:
    """AC-7: WorkItemBoardSnapshotWithDescription includes Description."""
    from ado_odata_async import (
        WorkItemBoardSnapshotWithDescription,  # type: ignore[import-untyped]  # reason: RED phase
    )

    row = {
        "WorkItemId": 1,
        "DateSK": 20260522,
        "BoardSK": 1,
        "BoardName": "Kanban",
        "BoardColumnName": "Doing",
        "BoardColumnOrder": 1,
        "State": "Active",
        "WorkItemType": "User Story",
        "IsCurrent": True,
        "Description": "Fix the login flow",
    }
    instance = WorkItemBoardSnapshotWithDescription.model_validate(row)
    assert instance.Description == "Fix the login flow"


# ── AC-8: Area model ────────────────────────────────────────


def test_ac8_area() -> None:
    """AC-8: Area has AreaSK (int) and AreaPath (str)."""
    from ado_odata_async import (
        Area,  # type: ignore[import-untyped]  # reason: RED phase
    )

    row = {
        "AreaSK": 1,
        "AreaId": "guid-789",
        "AreaPath": "Project\\Feature A",
        "AreaName": "Feature A",
    }
    instance = Area.model_validate(row)
    assert isinstance(instance.AreaSK, int)
    assert isinstance(instance.AreaPath, str)
    assert instance.AreaPath == "Project\\Feature A"


# ── AC-9: Date model ────────────────────────────────────────


def test_ac9_date() -> None:
    """AC-9: Date has DateSK (int YYYYMMDD) and Year (int)."""
    from ado_odata_async import (
        Date,  # type: ignore[import-untyped]  # reason: RED phase
    )

    row = {
        "DateSK": 20260522,
        "Date": "2026-05-22",
        "Year": 2026,
        "Month": 5,
        "Day": 22,
        "Quarter": 2,
        "DayOfWeek": 5,
        "MonthName": "May",
        "DayOfWeekName": "Friday",
        "WeekOfYear": 21,
    }
    instance = Date.model_validate(row)
    assert instance.DateSK == 20260522
    assert instance.Year == 2026


# ── AC-10: User model ───────────────────────────────────────


def test_ac10_user() -> None:
    """AC-10: User has UserSK (int) and UserName (str)."""
    from ado_odata_async import (
        User,  # type: ignore[import-untyped]  # reason: RED phase
    )

    row = {"UserSK": 1, "UserId": "guid-abc", "UserName": "user@example.com"}
    instance = User.model_validate(row)
    assert isinstance(instance.UserSK, int)
    assert isinstance(instance.UserName, str)


# ── AC-11: WorkItemType model ───────────────────────────────


def test_ac11_work_item_type() -> None:
    """AC-11: WorkItemType has WorkItemTypeSK (int) and WorkItemTypeName (str)."""
    from ado_odata_async import (
        WorkItemType,  # type: ignore[import-untyped]  # reason: RED phase
    )

    row = {"WorkItemTypeSK": 1, "WorkItemTypeName": "Bug"}
    instance = WorkItemType.model_validate(row)
    assert isinstance(instance.WorkItemTypeSK, int)
    assert isinstance(instance.WorkItemTypeName, str)


# ── AC-12: WorkItemLink model ───────────────────────────────


def test_ac12_work_item_link() -> None:
    """AC-12: WorkItemLink has SourceWorkItemId (int) and LinkType (str)."""
    from ado_odata_async import (
        WorkItemLink,  # type: ignore[import-untyped]  # reason: RED phase
    )

    row = {
        "WorkItemLinkId": 1,
        "SourceWorkItemId": 100,
        "TargetWorkItemId": 200,
        "LinkType": "Child",
    }
    instance = WorkItemLink.model_validate(row)
    assert isinstance(instance.SourceWorkItemId, int)
    assert isinstance(instance.LinkType, str)
    assert instance.LinkType == "Child"
