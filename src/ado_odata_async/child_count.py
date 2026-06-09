"""Child count & hierarchy depth — compute from WorkItemLinks hierarchy data."""

from __future__ import annotations

MAX_DEPTH = 100


def compute_child_count(links: list[dict[str, int]]) -> dict[int, int]:
    """Count direct children per parent from WorkItemLinks data.

    Iterates over link records and increments a counter for each
    SourceWorkItemId (parent).

    Args:
        links: List of link dicts with "SourceWorkItemId" and
            "TargetWorkItemId" integer keys.

    Returns:
        Dict mapping parent WorkItemId to its direct child count.
        Parents with no children are not included.
    """
    counts: dict[int, int] = {}
    for link in links:
        parent = link["SourceWorkItemId"]
        counts[parent] = counts.get(parent, 0) + 1
    return counts


def compute_hierarchy_depth(links: list[dict[str, int]]) -> dict[int, int]:
    """Compute depth from root for each node in a hierarchy DAG.

    Builds an adjacency list from links, identifies root nodes (those
    that are never a TargetWorkItemId), then performs iterative DFS
    to assign depth. Depth is capped at MAX_DEPTH (100).

    Args:
        links: List of link dicts with "SourceWorkItemId" and
            "TargetWorkItemId" integer keys.

    Returns:
        Dict mapping every WorkItemId in the link set to its depth
        from the nearest root. Roots have depth 0. Nodes not reachable
        from any root get depth 0.
    """
    if not links:
        return {}

    children: dict[int, list[int]] = {}
    all_ids: set[int] = set()
    child_ids: set[int] = set()

    for link in links:
        src = link["SourceWorkItemId"]
        tgt = link["TargetWorkItemId"]
        children.setdefault(src, []).append(tgt)
        all_ids.add(src)
        all_ids.add(tgt)
        child_ids.add(tgt)

    roots = all_ids - child_ids
    depth: dict[int, int] = {}

    for root in roots:
        stack = [(root, 0)]
        while stack:
            node, d = stack.pop()
            if node in depth:
                continue
            depth[node] = min(d, MAX_DEPTH)
            if d < MAX_DEPTH:
                for child in children.get(node, []):
                    if child not in depth:
                        stack.append((child, d + 1))

    for wid in all_ids:
        depth.setdefault(wid, 0)

    return depth
