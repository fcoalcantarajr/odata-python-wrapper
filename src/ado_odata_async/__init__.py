"""Async Python wrapper for Azure DevOps Analytics OData (v4.0-preview)."""

from importlib.metadata import version as _version

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
    "ODATA_VERSION",
    "AdoODataClient",
    "AdoODataError",
    "Area",
    "AuthenticationError",
    "BadRequestError",
    "Date",
    "Iteration",
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
]

__version__ = _version(__package__)
