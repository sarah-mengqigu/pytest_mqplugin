"""GitHub pytest fixtures."""

from __future__ import annotations

from typing import cast

import pytest

from ..bootstrap import ServiceManager
from ..services.github import GithubClient


@pytest.fixture(scope="session")
def github_client(service_manager: ServiceManager) -> GithubClient:
    """Return the configured GitHub service for tests."""
    return cast(GithubClient, service_manager.get("github"))
