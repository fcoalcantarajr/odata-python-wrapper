"""Integration test configuration — skip unless --run-integration is passed."""

from __future__ import annotations

import pytest


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip integration tests unless --run-integration is passed."""
    if config.getoption("--run-integration", default=False):
        return
    skip_integration = pytest.mark.skip(reason="need --run-integration option to run")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add --run-integration option."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="run integration tests that require live Azure DevOps access",
    )
