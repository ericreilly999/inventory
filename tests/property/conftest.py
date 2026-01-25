"""Property tests configuration.

Property tests use their own database setup and don't need the unit test fixtures.
This conftest prevents the parent conftest fixtures from being used and configures
pytest to avoid asyncio mode conflicts with hypothesis.
"""

import pytest


def pytest_collection_modifyitems(items):
    """Mark all property tests to skip asyncio mode.

    This prevents pytest-asyncio from trying to inspect hypothesis-decorated
    functions, which causes AttributeError: 'function' object has no attribute
    'hypothesis'.
    """
    for item in items:
        # Skip asyncio mode for all property tests
        if "property" in str(item.fspath):
            item.add_marker(pytest.mark.no_cover)
