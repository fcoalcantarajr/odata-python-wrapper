"""Dependency graph — fetch WorkItemLinks, build dependency maps, resolve titles, flag overdue."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

from ado_odata_async.client import AdoODataClient

logger = logging.getLogger(__name__)

BATCH_SIZE = 200


def _chunk_ids(ids: list[int], size: int) -> list[list[int]]:
    """Split ids into chunks of *size*."""
    return [ids[i : i + size] for i in range(0, len(ids), size)]


async def _fetch_workitems(
    client: AdoODataClient,
    ids: list[int],
) -> list[dict[str, Any]]:
    """Fetch work items by IDs for title / overdue resolution."""
    if not ids:
        return []
    or_exprs = [f"WorkItemId eq {i}" for i in ids]
    data = await client.get(
        "WorkItems",
        **{
            "$filter": " or ".join(or_exprs),
            "$select": "WorkItemId,Title,ClosedDate,TargetDate",
        },
    )
    value = data.get("value", [])
    return list(value)


def _add_overdue_flags(
    result: dict[int, dict[str, list[Any]]],
    items: list[dict[str, Any]],
) -> None:
    """Add risk flags for overdue blockers."""
    today = date.today()
    overdue_ids: set[int] = set()
    for item in items:
        wid = item["WorkItemId"]
        closed = item.get("ClosedDate")
        target = item.get("TargetDate")
        if closed is None and target is not None:
            try:
                target_date = date.fromisoformat(target)
                if target_date < today:
                    overdue_ids.add(wid)
            except (ValueError, TypeError):
                continue
    for _wid, entry in result.items():
        for blocker in entry["blocks"]:
            blocker_id = blocker["id"] if isinstance(blocker, dict) else blocker
            if blocker_id in overdue_ids:
                entry["risk_flags"].append(f"overdue_blocker:{blocker_id}")


async def fetch_dependency_links(
    client: AdoODataClient,
    work_item_ids: list[int],
    *,
    resolve_titles: bool = False,
    flag_overdue: bool = False,
    link_type: str | None = None,
) -> dict[int, dict[str, list[Any]]]:
    """Fetch dependency links for a batch of work items.

    Args:
        client: An active ``AdoODataClient`` (inside ``async with`` context).
        work_item_ids: Work item IDs to fetch links for.
        resolve_titles: If ``True``, resolve link-target titles.
        flag_overdue: If ``True``, flag overdue blockers as risk.
        link_type: If set, only include links with this
            ``LinkTypeReferenceName``.

    Returns:
        Dict mapping each ``workItemId`` to
        ``{"depends_on": [...], "blocks": [...], "risk_flags": [...]}``.
    """
    result: dict[int, dict[str, list[Any]]] = {
        wid: {"depends_on": [], "blocks": [], "risk_flags": []} for wid in work_item_ids
    }
    for chunk in _chunk_ids(work_item_ids, BATCH_SIZE):
        or_exprs = [f"SourceWorkItemId eq {i}" for i in chunk]
        or_exprs += [f"TargetWorkItemId eq {i}" for i in chunk]
        data = await client.get(
            "WorkItemLinks",
            **{"$filter": " or ".join(or_exprs)},
        )
        for link in data.get("value", []):
            ref_name = link.get("LinkTypeReferenceName")
            if link_type is not None and ref_name != link_type:
                continue
            source: int = link["SourceWorkItemId"]
            target: int = link["TargetWorkItemId"]
            result[source]["blocks"].append(target)
            result[target]["depends_on"].append(source)
    if resolve_titles or flag_overdue:
        items = await _fetch_workitems(client, list(result.keys()))
        titles: dict[int, str] = {i["WorkItemId"]: i.get("Title", "") for i in items}
        if resolve_titles:
            for entry in result.values():
                entry["blocks"] = [{"id": x, "title": titles.get(x, "")} for x in entry["blocks"]]
                entry["depends_on"] = [
                    {"id": x, "title": titles.get(x, "")} for x in entry["depends_on"]
                ]
        if flag_overdue:
            _add_overdue_flags(result, items)
    return result
