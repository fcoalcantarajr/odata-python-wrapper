"""Async Python wrapper for Azure DevOps Analytics OData (v4.0-preview)."""

from importlib.metadata import version as _version

from ado_odata_async.baseline_target import BaselineResult, compute_baseline_metrics
from ado_odata_async.child_count import compute_child_count, compute_hierarchy_depth
from ado_odata_async.client import ODATA_VERSION, AdoODataClient
from ado_odata_async.dependency_graph import fetch_dependency_links
from ado_odata_async.entities import (
    Area,
    Date,
    Iteration,
    Project,
    Team,
    User,
    WorkItem,
    WorkItemBoardSnapshot,
    WorkItemBoardSnapshotWithDescription,
    WorkItemLink,
    WorkItemRevisions,
    WorkItemType,
)
from ado_odata_async.exceptions import (
    AdoODataError,
    AuthenticationError,
    BadRequestError,
    RateLimitError,
    TransientError,
)
from ado_odata_async.flow_times import FlowTimeResult, compute_flow_times
from ado_odata_async.plan_history import PlanHistoryResult, compute_plan_history

__all__ = [
    "ODATA_VERSION",
    "AdoODataClient",
    "AdoODataError",
    "Area",
    "AuthenticationError",
    "BadRequestError",
    "BaselineResult",
    "Date",
    "FlowTimeResult",
    "Iteration",
    "PlanHistoryResult",
    "Project",
    "RateLimitError",
    "Team",
    "TransientError",
    "User",
    "WorkItem",
    "WorkItemBoardSnapshot",
    "WorkItemBoardSnapshotWithDescription",
    "WorkItemLink",
    "WorkItemRevisions",
    "WorkItemType",
    "compute_baseline_metrics",
    "compute_child_count",
    "compute_flow_times",
    "compute_hierarchy_depth",
    "compute_plan_history",
    "fetch_dependency_links",
]

__version__ = _version(__package__)
