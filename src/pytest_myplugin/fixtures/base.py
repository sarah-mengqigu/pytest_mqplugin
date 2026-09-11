"""Shared pytest fixtures for managed services."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from ..bootstrap import ServiceManager


@pytest.fixture(scope="session")
def service_manager() -> Iterator[ServiceManager]:
    """Create and dispose the session-scoped service manager."""
    manager = ServiceManager()
    try:
        yield manager
    finally:
        manager.close()
