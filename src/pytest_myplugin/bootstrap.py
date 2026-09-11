"""Application wiring for configuration and service lifecycle management."""

from __future__ import annotations

from collections.abc import Mapping
from types import TracebackType
from typing import Any

from .config import ServiceConfig, load_service_config
from .services import GithubClient, build_github_client
from .services.base import Service
from .services.registry import ServiceRegistry


class ServiceManager:
    """Lazily build, cache, and close configured SDK services."""

    def __init__(
        self,
        service_config: Mapping[str, Mapping[str, Any]] | None = None,
        registry: ServiceRegistry | None = None,
    ) -> None:
        self._config = (
            dict(service_config)
            if service_config is not None
            else load_service_config()
        )
        self._registry = registry or _default_registry()
        self._services: dict[str, Service] = {}

    def get(self, name: str) -> Service:
        """Return a cached service, creating it on first use."""
        if name not in self._config:
            raise KeyError(f"Service {name!r} is not configured")

        if name not in self._services:
            service = self._registry.build(name, self._config[name])
            if not isinstance(service, Service):
                raise TypeError(f"Service {name!r} does not implement Service")
            self._services[name] = service
        return self._services[name]

    def close(self) -> None:
        """Close all created services in reverse creation order."""
        for service in reversed(tuple(self._services.values())):
            service.close()
        self._services.clear()

    def __enter__(self) -> ServiceManager:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()


def _default_registry() -> ServiceRegistry:
    registry = ServiceRegistry()
    registry.register("github", build_github_client)
    return registry


__all__ = ["GithubClient", "ServiceConfig", "ServiceManager"]
