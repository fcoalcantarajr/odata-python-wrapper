"""Async Python wrapper for Azure DevOps Analytics OData (v4.0-preview)."""

from ado_odata_async.client import ODATA_VERSION, AdoODataClient
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

__all__ = [
    "AdoODataClient",
    "ODATA_VERSION",
    "WorkItem",
    "WorkItemRevisions",
    "WorkItemBoardSnapshot",
    "WorkItemBoardSnapshotWithDescription",
    "Iteration",
    "Project",
    "Team",
    "Area",
    "Date",
    "User",
    "WorkItemType",
    "WorkItemLink",
    "AdoODataError",
    "AuthenticationError",
    "BadRequestError",
    "RateLimitError",
    "TransientError",
]

__version__ = "0.0.1"
