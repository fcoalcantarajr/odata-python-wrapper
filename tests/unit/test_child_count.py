"""Tests for SPEC-015: Child count & hierarchy depth computation."""

from __future__ import annotations

from ado_odata_async.child_count import (
    compute_child_count,
    compute_hierarchy_depth,
)


def _link(source: int, target: int) -> dict[str, int]:
    return {"SourceWorkItemId": source, "TargetWorkItemId": target}


class TestAC1ChildCount:
    def test_single_parent(self) -> None:
        links = [_link(1, 2), _link(1, 3), _link(1, 4)]
        result = compute_child_count(links)
        assert result == {1: 3}

    def test_multiple_parents(self) -> None:
        links = [_link(1, 2), _link(1, 3), _link(2, 4)]
        result = compute_child_count(links)
        assert result == {1: 2, 2: 1}

    def test_no_links(self) -> None:
        result = compute_child_count([])
        assert result == {}


class TestAC2HierarchyDepth:
    def test_flat_tree(self) -> None:
        links = [_link(1, 2), _link(1, 3)]
        result = compute_hierarchy_depth(links)
        assert result == {1: 0, 2: 1, 3: 1}

    def test_deep_tree(self) -> None:
        links = [_link(1, 2), _link(2, 3), _link(3, 4)]
        result = compute_hierarchy_depth(links)
        assert result == {1: 0, 2: 1, 3: 2, 4: 3}

    def test_multiple_roots(self) -> None:
        links = [_link(1, 2), _link(3, 4)]
        result = compute_hierarchy_depth(links)
        assert result[1] == 0
        assert result[3] == 0


class TestAC3CircularReferences:
    def test_cycle_capped_at_100(self) -> None:
        links = [_link(1, 2), _link(2, 3), _link(3, 1)]
        result = compute_hierarchy_depth(links)
        assert all(d <= 100 for d in result.values())


class TestAC4EmptyLinks:
    def test_empty_child_count(self) -> None:
        assert compute_child_count([]) == {}

    def test_empty_hierarchy_depth(self) -> None:
        assert compute_hierarchy_depth([]) == {}
