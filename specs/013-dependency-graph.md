<!-- notion-page-id: -->
<!-- last-sync-hash: -->

# SPEC-013: Dependency graph per card — fetch and normalize Predecessor/Successor links

- id: SPEC-013
- slug: dependency-graph
- status: IMPLEMENTED
- created: 2026-06-05
- owner: @opencode

## User Story

As a delivery plan consumer, I want each card to expose its dependency graph (which cards block it, which cards it blocks), so that I can identify critical path bottlenecks and stale blockers without manual graph traversal.

## Use Cases

- UC1: Fetch Predecessor/Successor links for a batch of work items.
- UC2: Normalize links into `depends_on` (IDs blocking this card) and `blocks` (IDs this card blocks).
- UC3: Resolve link-target titles within the fetched set where possible.
- UC4: Flag dependencies whose blocker is overdue or stalled as highest-risk.
- UC5: Build a reusable links-fetch component (SPEC-015 reuses it for child counting).

## Acceptance Criteria (Gherkin absoluto)

### AC-1: Fetch dependency links for a batch of work items

```
Given a batch of 3 work item IDs [101, 102, 103]
  And mock HTTP returns WorkItemLinks with:
    - SourceWorkItemId=101, TargetWorkItemId=102, LinkTypeReferenceName="System.LinkTypes.Dependency-Forward"
    - SourceWorkItemId=103, TargetWorkItemId=101, LinkTypeReferenceName="System.LinkTypes.Dependency-Reverse"
When await fetch_dependency_links(client, [101, 102, 103])
Then result contains 2 links
  And link for 101 has depends_on=[103] and blocks=[102]
  And link for 102 has depends_on=[101] and blocks=[]
  And link for 103 has depends_on=[] and blocks=[101]
```

### AC-2: Handle work items with no dependencies

```
Given a batch of 2 work item IDs [201, 202]
  And mock HTTP returns empty WorkItemLinks
When await fetch_dependency_links(client, [201, 202])
Then result contains 0 links
  And link for 201 has depends_on=[] and blocks=[]
  And link for 202 has depends_on=[] and blocks=[]
```

### AC-3: Page work items in batches of 200

```
Given a batch of 250 work item IDs
When await fetch_dependency_links(client, list_of_250_ids)
Then client.get() is called 2 times
  And first call has $filter containing first 200 IDs
  And second call has $filter containing last 50 IDs
```

### AC-4: Handle HTTP 429 with Retry-After

```
Given mock HTTP returns 429 with Retry-After: 1 on first call
  And mock HTTP returns 200 with links on second call
When await fetch_dependency_links(client, [101])
Then result contains the links from second call
  And total wait time is approximately 1 second
```

### AC-5: Resolve link-target titles within fetched set

```
Given a batch of 3 work item IDs [101, 102, 103]
  And mock HTTP returns WorkItemLinks with SourceWorkItemId=101, TargetWorkItemId=102
  And mock HTTP returns WorkItems with [{WorkItemId:101, Title:"Card A"}, {WorkItemId:102, Title:"Card B"}]
When await fetch_dependency_links(client, [101, 102, 103], resolve_titles=True)
Then link for 101 has blocks=[{"id": 102, "title": "Card B"}]
```

### AC-6: Flag overdue blocker as highest-risk

```
Given a batch of 3 work item IDs [101, 102, 103]
  And WorkItem 102 has ClosedDate=None and TargetDate="2026-06-01" (overdue)
  And WorkItem 101 depends on 102
When await fetch_dependency_links(client, [101, 102, 103], flag_overdue=True)
Then link for 101 has risk_flags=["overdue_blocker:102"]
```

### AC-7: Reusable component for SPEC-015 (child counting)

```
Given the fetch_dependency_links function
When called with link_type="System.LinkTypes.Hierarchy-Forward"
Then only hierarchy links are returned (not dependency links)
```

## NFRs

- **Performance:** Fetching 200 work items' links completes in < 5s with mock HTTP.
- **Security:** PAT never logged or committed; mask in debug logs (HR-16).
- **Observability:** Structured log in DEBUG shows batch size and link count.
- **Maintainability:** `fetch_dependency_links` is a standalone async function in its own module; function is kept under 50 lines, ≤5 parameters, complexity ≤10.

## INVEST self-score

- **I**ndependent: 8/10 — Depends on client and WorkItemLink entity (existing), but self-contained.
- **N**egotiable: 8/10 — Link type names and risk flag format are negotiable.
- **V**aluable: 9/10 — Dependency graph is highest diagnostic value for delivery plans.
- **E**stimable: 8/10 — Clear pattern from existing pagination code.
- **S**mall: 8/10 — ~100 lines (test + function + module); fits in one session.
- **T**estable: 10/10 — All ACs testable with aioresponses + mock payloads.

Média: 8.5/10 (mínimo 8 pra `APPROVED`)

## Out-of-scope

- Circular dependency detection (future enhancement).
- Cross-project/org dependencies (System.LinkTypes.Remote.Dependency-*).
- Real-time dependency updates (polling or webhooks).
- Full graph visualization (downstream consumer responsibility).

## Test plan

- AC-1 → `tests/unit/test_dependency_graph.py::test_ac1_fetch_links_batch`
- AC-2 → `tests/unit/test_dependency_graph.py::test_ac2_no_dependencies`
- AC-3 → `tests/unit/test_dependency_graph.py::test_ac3_page_200`
- AC-4 → `tests/unit/test_dependency_graph.py::test_ac4_retry_after_429`
- AC-5 → `tests/unit/test_dependency_graph.py::test_ac5_resolve_titles`
- AC-6 → `tests/unit/test_dependency_graph.py::test_ac6_flag_overdue`
- AC-7 → `tests/unit/test_dependency_graph.py::test_ac7_hierarchy_link_type`

## DoD

- [ ] Todos AC verdes em `uv run pytest -q tests/unit/test_dependency_graph.py`
- [ ] Coverage do módulo `src/ado_odata_async/dependency_graph.py` ≥ 85%
- [ ] `ruff check .`, `mypy src/` exit 0
- [ ] `bash scripts/audit.sh` exit 0
- [ ] HR-6 (async-only), HR-7 (single ClientSession), HR-16 (PAT mask), HR-21 (coverage) respeitadas
- [ ] Conventional Commit emitido por `git-keeper` referenciando `(SPEC-013)`
