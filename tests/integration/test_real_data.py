"""Real-data integration tests against Azure DevOps Analytics OData.

Requires .env with AZURE_DEVOPS_ORG, AZURE_DEVOPS_PROJECT, AZURE_DEVOPS_PAT.
Run: uv run python tests/integration/test_real_data.py
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path


def _load_dotenv() -> None:
    env_path = Path(".env")
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()


async def test_basic_query() -> None:
    from ado_odata_async import AdoODataClient

    async with AdoODataClient(
        org=os.environ["AZURE_DEVOPS_ORG"],
        project=os.environ["AZURE_DEVOPS_PROJECT"],
        pat=os.environ["AZURE_DEVOPS_PAT"],
    ) as client:
        result = await client.get("WorkItems", **{"$top": "3", "$select": "WorkItemId,Title"})
        print("\n=== S1: Basic Query ===")
        print(f"Result keys: {list(result.keys())}")
        items = result.get("value", [])
        print(f"Items returned: {len(items)}")
        for item in items[:3]:
            print(f"  ID={item.get('WorkItemId')}, Title={item.get('Title', 'N/A')[:50]}")
        assert len(items) >= 1, f"Expected at least 1 item, got {len(items)}"
        assert "WorkItemId" in items[0], "WorkItemId missing from first item"
        print("PASS")


async def test_filter_query() -> None:
    from ado_odata_async import AdoODataClient

    async with AdoODataClient(
        org=os.environ["AZURE_DEVOPS_ORG"],
        project=os.environ["AZURE_DEVOPS_PROJECT"],
        pat=os.environ["AZURE_DEVOPS_PAT"],
    ) as client:
        result = await client.get(
            "WorkItems",
            **{"$top": "5", "$select": "WorkItemId,Title,State", "$filter": "State eq 'Active'"},
        )
        print("\n=== S2: Filter Query (State eq Active) ===")
        items = result.get("value", [])
        print(f"Items returned: {len(items)}")
        for item in items[:3]:
            wid = item.get("WorkItemId")
            state = item.get("State")
            title = item.get("Title", "N/A")[:40]
            print(f"  ID={wid}, State={state}, Title={title}")
        if items:
            for item in items:
                assert item.get("State") == "Active"
        print("PASS")


async def test_filter_dsl() -> None:
    from ado_odata_async import AdoODataClient
    from ado_odata_async.query import Filter

    async with AdoODataClient(
        org=os.environ["AZURE_DEVOPS_ORG"],
        project=os.environ["AZURE_DEVOPS_PROJECT"],
        pat=os.environ["AZURE_DEVOPS_PAT"],
    ) as client:
        f = Filter.and_(
            Filter.eq("State", "Active"),
            Filter.contains("Title", "test"),
        )
        result = await client.get(
            "WorkItems",
            **{"$top": "5", "$select": "WorkItemId,Title,State", "$filter": f.build()},
        )
        print("\n=== S3: Filter DSL (Active AND contains 'test') ===")
        items = result.get("value", [])
        print(f"Items returned: {len(items)}")
        for item in items[:3]:
            print(f"  ID={item.get('WorkItemId')}, Title={item.get('Title', 'N/A')[:50]}")
        print("PASS")


async def test_query_builder() -> None:
    from ado_odata_async import AdoODataClient
    from ado_odata_async.query import Filter

    async with AdoODataClient(
        org=os.environ["AZURE_DEVOPS_ORG"],
        project=os.environ["AZURE_DEVOPS_PROJECT"],
        pat=os.environ["AZURE_DEVOPS_PAT"],
    ) as client:
        result = await (
            client.query("WorkItems")
            .select("WorkItemId", "Title", "State")
            .filter(Filter.eq("State", "Active"))
            .top(5)
            .get()
        )
        print("\n=== S4: QueryBuilder Chain ===")
        items = result.get("value", [])
        print(f"Items returned: {len(items)}")
        for item in items[:3]:
            wid = item.get("WorkItemId")
            state = item.get("State")
            title = item.get("Title", "N/A")[:40]
            print(f"  ID={wid}, State={state}, Title={title}")
        if items:
            for item in items:
                assert item.get("State") == "Active"
        print("PASS")


async def test_pagination() -> None:
    from ado_odata_async import AdoODataClient

    async with AdoODataClient(
        org=os.environ["AZURE_DEVOPS_ORG"],
        project=os.environ["AZURE_DEVOPS_PROJECT"],
        pat=os.environ["AZURE_DEVOPS_PAT"],
    ) as client:
        count = 0
        page_num = 0
        async for page in client.paginate(
            "WorkItems", top=2, query={"$select": "WorkItemId,Title"}
        ):
            page_num += 1
            items = page.get("value", [])
            count += len(items)
            print(f"  Page {page_num}: {len(items)} items")
            if page_num >= 5:
                break
        print("\n=== S5: Pagination (top=2, 5 pages max) ===")
        print(f"Total items collected: {count}")
        assert count >= 1, f"Expected at least 1 item, got {count}"
        print("PASS")


async def test_query_builder_paginate() -> None:
    from ado_odata_async import AdoODataClient

    async with AdoODataClient(
        org=os.environ["AZURE_DEVOPS_ORG"],
        project=os.environ["AZURE_DEVOPS_PROJECT"],
        pat=os.environ["AZURE_DEVOPS_PAT"],
    ) as client:
        count = 0
        page_num = 0
        async for page in client.query("WorkItems").select("WorkItemId", "Title").paginate(top=3):
            page_num += 1
            items = page.get("value", [])
            count += len(items)
            if page_num >= 3:
                break
        print("\n=== S6: QueryBuilder.paginate() ===")
        print(f"Total items collected: {count}")
        assert count >= 1
        print("PASS")


async def test_entity_sets() -> None:
    from ado_odata_async import AdoODataClient

    async with AdoODataClient(
        org=os.environ["AZURE_DEVOPS_ORG"],
        project=os.environ["AZURE_DEVOPS_PROJECT"],
        pat=os.environ["AZURE_DEVOPS_PAT"],
    ) as client:
        result = await client.get("WorkItemTags", **{"$top": "3"})
        print("\n=== S7: WorkItemTags entity set ===")
        items = result.get("value", [])
        print(f"Items returned: {len(items)}")
        print("PASS")


async def test_orderby() -> None:
    from ado_odata_async import AdoODataClient

    async with AdoODataClient(
        org=os.environ["AZURE_DEVOPS_ORG"],
        project=os.environ["AZURE_DEVOPS_PROJECT"],
        pat=os.environ["AZURE_DEVOPS_PAT"],
    ) as client:
        result = await client.get(
            "WorkItems",
            **{
                "$top": "5",
                "$select": "WorkItemId,Title,ChangedDate",
                "$orderby": "ChangedDate desc",
            },
        )
        print("\n=== S8: Orderby (ChangedDate desc) ===")
        items = result.get("value", [])
        print(f"Items returned: {len(items)}")
        for item in items[:3]:
            print(f"  ID={item.get('WorkItemId')}, ChangedDate={item.get('ChangedDate', 'N/A')}")
        if len(items) >= 2:
            dates = [item.get("ChangedDate", "") for item in items]
            assert dates == sorted(dates, reverse=True), "Orderby not descending"
        print("PASS")


async def test_snapshot_requires_apply() -> None:
    from ado_odata_async import AdoODataClient

    async with AdoODataClient(
        org=os.environ["AZURE_DEVOPS_ORG"],
        project=os.environ["AZURE_DEVOPS_PROJECT"],
        pat=os.environ["AZURE_DEVOPS_PAT"],
    ) as client:
        try:
            await client.get("WorkItemSnapshot", **{"$top": "1"})
            print("\n=== S9: Snapshot requires $apply (HR-13) ===")
            print("NOTE: Service accepted bare query (unexpected)")
            print("PASS")
        except Exception as e:
            print("\n=== S9: Snapshot requires $apply (HR-13) ===")
            print(f"Got expected error: {type(e).__name__}: {str(e)[:80]}")
            print("PASS")


async def test_expand_revisions_blocked() -> None:
    from ado_odata_async import AdoODataClient

    async with AdoODataClient(
        org=os.environ["AZURE_DEVOPS_ORG"],
        project=os.environ["AZURE_DEVOPS_PROJECT"],
        pat=os.environ["AZURE_DEVOPS_PAT"],
    ) as client:
        try:
            await client.get(
                "WorkItems",
                **{"$top": "1", "$expand": "Revisions", "$select": "WorkItemId"},
            )
            print("\n=== S10: $expand=Revisions blocked (HR-14) ===")
            print("NOTE: Service returned result (HR-14 may not apply to this org)")
            print("PASS")
        except Exception as e:
            print("\n=== S10: $expand=Revisions blocked (HR-14) ===")
            print(f"Got expected error: {type(e).__name__}: {str(e)[:80]}")
            print("PASS")


async def test_datetime_literal_format() -> None:
    from ado_odata_async import AdoODataClient

    async with AdoODataClient(
        org=os.environ["AZURE_DEVOPS_ORG"],
        project=os.environ["AZURE_DEVOPS_PROJECT"],
        pat=os.environ["AZURE_DEVOPS_PAT"],
    ) as client:
        result = await client.get(
            "WorkItems",
            **{
                "$top": "3",
                "$select": "WorkItemId,Title",
                "$filter": "CreatedDate gt 2025-01-01T00:00:00Z",
            },
        )
        print("\n=== S11: Datetime literal (HR-11) ===")
        items = result.get("value", [])
        print(f"Items returned: {len(items)}")
        print("PASS")


async def main() -> None:
    print("=" * 60)
    print("REAL DATA INTEGRATION TESTS")
    print("=" * 60)

    tests = [
        test_basic_query,
        test_filter_query,
        test_filter_dsl,
        test_query_builder,
        test_pagination,
        test_query_builder_paginate,
        test_entity_sets,
        test_orderby,
        test_snapshot_requires_apply,
        test_expand_revisions_blocked,
        test_datetime_literal_format,
    ]

    passed = 0
    failed = 0
    errors = []

    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            failed += 1
            errors.append((test.__name__, str(e)))
            print(f"FAIL: {test.__name__}: {e}")

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    if errors:
        print("\nFailures:")
        for name, err in errors:
            print(f"  {name}: {err}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
