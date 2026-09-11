"""Core pytest hooks for the example plugin."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from . import __version__
from .fixtures.base import service_manager
from .fixtures.github import github_client
from .fixtures.github_ui import github_logged_in_page

__all__ = [
    "github_client",
    "github_logged_in_page",
    "service_manager",
]


@dataclass(frozen=True, slots=True)
class MyPluginConfig:
    """Public configuration exposed through the ``myplugin_config`` fixture."""

    enabled: bool
    rootpath: Path
    version: str = __version__


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register command-line options."""
    group = parser.getgroup("myplugin")
    group.addoption(
        "--myplugin",
        action="store_true",
        default=False,
        help="enable the pytest-myplugin example behavior",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Register markers and initialize plugin-specific state."""
    config.addinivalue_line(
        "markers",
        "myplugin: mark tests affected by the pytest-myplugin example behavior",
    )


@pytest.fixture
def myplugin_config(pytestconfig: pytest.Config) -> MyPluginConfig:
    """Expose plugin configuration to tests."""
    return MyPluginConfig(
        enabled=bool(pytestconfig.getoption("--myplugin")),
        rootpath=pytestconfig.rootpath,
    )


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Apply the example marker when the plugin is explicitly enabled."""
    if not config.getoption("--myplugin"):
        return

    marker = pytest.mark.myplugin
    for item in items:
        item.add_marker(marker)


def pytest_report_header(config: pytest.Config) -> str | None:
    """Show the plugin version in pytest's report header when enabled."""
    if config.getoption("--myplugin"):
        return f"pytest-myplugin: {__version__}"
    return None
