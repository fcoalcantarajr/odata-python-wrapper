"""GREEN: SR-001 session-exit pagination guard (fixed bd996e2)."""

import pytest

from ado_odata_async import AdoODataClient


@pytest.mark.asyncio
async def test_pagination_after_context_exit_raises_runtime_error(
    fake_org: str,
    fake_project: str,
    fake_pat: str,
) -> None:
    """SR-001: Using pagination after client context exits should raise RuntimeError.

    Scenario:
      1. Create client and enter context
      2. Exit context (session closes)
      3. Try to iterate pagination generator
      4. Should raise RuntimeError with clear message, not AttributeError
    """
    client = AdoODataClient(org=fake_org, project=fake_project, pat=fake_pat)

    # Enter and exit context
    async with client:
        pass

    # Now try to paginate — client._session is None
    # This MUST raise RuntimeError, not AttributeError
    async def consume_pagination() -> None:
        async for _ in client.paginate("WorkItems", top=100):
            pass

    with pytest.raises(RuntimeError, match="session"):
        await consume_pagination()
