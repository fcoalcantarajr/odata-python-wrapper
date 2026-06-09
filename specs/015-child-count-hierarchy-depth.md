<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# SPEC-015: Child Count & Hierarchy Depth

- id: SPEC-015
- slug: child-count-hierarchy-depth
- status: IMPLEMENTED
- created: 2026-06-05
- owner: @sisyphus

## User Story

As a delivery lead, I want to compute child counts and hierarchy depth from work item link data, so that I can assess portfolio structure and work breakdown granularity.

## Use Cases

- UC1: Compute `child_count` per work item from Hierarchy-Forward links
- UC2: Compute `hierarchy_depth` (distance from root) for each work item
- UC3: Handle circular references gracefully (depth capped at a max threshold)
- UC4: Handle empty link sets (return empty dicts)

## Acceptance Criteria (Gherkin absoluto)

### AC-1: Compute child_count

```
Given a list of hierarchy links with SourceWorkItemId and TargetWorkItemId
When I call compute_child_count with those links
Then the result maps each parent ID to the count of its direct children
```

### AC-2: Compute hierarchy_depth

```
Given a list of hierarchy links forming a tree structure
When I call compute_hierarchy_depth with those links
Then the result maps each work item ID to its depth (root items have depth 0)
```

### AC-3: Handle circular references

```
Given a list of hierarchy links containing a cycle (A→B→C→A)
When I call compute_hierarchy_depth with those links
Then no work item has depth greater than 100
```

### AC-4: Handle empty links

```
Given an empty list of hierarchy links
When I call compute_child_count and compute_hierarchy_depth with those links
Then both results are empty dicts
```

## NFRs

- **Performance:** Computation completes in O(V + E) time where V = work items, E = links
- **Security:** Pure computation on already-fetched data
- **Observability:** N/A (synchronous utility functions)

## INVEST self-score

- **I**ndependent: 9/10 — Pure computation on link data
- **N**egotiable: 8/10 — Depth threshold could vary
- **V**aluable: 9/10 — Core metrics for hierarchy analysis
- **E**stimable: 9/10 — Clear input/output specification
- **S**mall: 9/10 — Two focused functions
- **T**estable: 10/10 — Deterministic input/output

Média: 9.0/10 (APPROVED)

## Out-of-scope

- Link fetching (uses data from SPEC-013's fetch_dependency_links)
- Cycle detection beyond depth capping
- Portfolio-level aggregation

## Test plan

- AC-1 → `tests/unit/test_child_count.py::test_ac1_child_count`
- AC-2 → `tests/unit/test_child_count.py::test_ac2_hierarchy_depth`
- AC-3 → `tests/unit/test_child_count.py::test_ac3_circular_references`
- AC-4 → `tests/unit/test_child_count.py::test_ac4_empty_links`

## DoD

- [ ] Todos AC verdes em `uv run pytest -q tests/unit/test_child_count.py`
- [ ] Coverage do módulo tocado ≥ 85%
- [ ] `ruff check .`, `mypy src/` exit 0
- [ ] `bash scripts/audit.sh` exit 0
- [ ] HARD RULES respeitadas: HR-3 (test first), HR-24 (functions ≤50 lines)
- [ ] Conventional Commit emitido por `git-keeper` referenciando `(SPEC-015)`
