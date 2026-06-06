"""Child count & hierarchy depth — compute from WorkItemLinks hierarchy data."""

from __future__ import annotations

MAX_DEPTH = 100


def compute_child_count(links: list[dict[str, int]]) -> dict[int, int]:
    counts: dict[int, int] = {}
    for link in links:
        parent = link["SourceWorkItemId"]
        counts[parent] = counts.get(parent, 0) + 1
    return counts


def compute_hierarchy_depth(links: list[dict[str, int]]) -> dict[int, int]:
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
