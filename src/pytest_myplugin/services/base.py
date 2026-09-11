"""Shared service contracts."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Service(Protocol):
    """Protocol implemented by all managed SDK services."""

    def close(self) -> None:
        """Release resources held by the service."""


ServiceBuilder = Callable[[Mapping[str, Any]], Service]
