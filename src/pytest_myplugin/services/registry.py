"""Registry mapping service names to SDK builders."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .base import Service, ServiceBuilder


class ServiceRegistry:
    """Store service builders and create configured SDK services."""

    def __init__(self) -> None:
        self._builders: dict[str, ServiceBuilder] = {}

    def register(self, name: str, builder: ServiceBuilder) -> None:
        """Register a builder for a service name."""
        if name in self._builders:
            raise ValueError(f"Service {name!r} is already registered")
        self._builders[name] = builder

    def build(self, name: str, config: Mapping[str, Any]) -> Service:
        """Build a registered service from a configuration section."""
        try:
            builder = self._builders[name]
        except KeyError as error:
            raise KeyError(f"Unknown service: {name!r}") from error
        return builder(config)

    @property
    def names(self) -> tuple[str, ...]:
        """Return the registered service names."""
        return tuple(self._builders)
