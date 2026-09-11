"""Load and merge service configuration files."""

from __future__ import annotations

import os
from collections.abc import Mapping
from importlib.resources import files
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10
    import tomli as tomllib

from .errors import ConfigError
from .resolver import resolve_environment

ServiceConfig = dict[str, dict[str, Any]]


def load_service_config(*paths: str | Path) -> ServiceConfig:
    """Load the packaged defaults and optional overriding configuration files.

    Explicit paths override the default files. When no paths are supplied,
    ``TEST_SERVICE_CONFIG`` is checked first, followed by
    ``config/services.toml`` and ``config/services.local.toml`` in the current
    working directory.
    """
    config = _load_toml(
        files("pytest_myplugin.config").joinpath("default.toml"),
    )
    candidate_paths, required = _candidate_paths(paths)

    for candidate_path in candidate_paths:
        path = Path(candidate_path)
        if not path.exists():
            if required:
                raise FileNotFoundError(f"Service config file not found: {path}")
            continue
        _deep_merge(config, _load_toml(path))

    resolved_config = resolve_environment(config)
    if not isinstance(resolved_config, Mapping):
        raise ConfigError("Service configuration must be a TOML table")

    return _service_sections(resolved_config)


def _candidate_paths(paths: tuple[str | Path, ...]) -> tuple[list[str | Path], bool]:
    if paths:
        return list(paths), True

    environment_path = os.getenv("TEST_SERVICE_CONFIG")
    if environment_path:
        return [environment_path], True

    project_config = Path.cwd() / "config"
    return [
        project_config / "services.toml",
        project_config / "services.local.toml",
    ], False


def _load_toml(path: Any) -> dict[str, Any]:
    with path.open("rb") as config_file:
        config = tomllib.load(config_file)

    if not isinstance(config, dict):
        raise ConfigError(f"Configuration file must contain a TOML table: {path}")
    return config


def _deep_merge(target: dict[str, Any], override: Mapping[str, Any]) -> None:
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(target.get(key), dict):
            _deep_merge(target[key], value)
        else:
            target[key] = value


def _service_sections(config: Mapping[str, Any]) -> ServiceConfig:
    services = config.get("services")
    if not isinstance(services, Mapping):
        raise ConfigError("Configuration must contain a [services] table")

    sections: ServiceConfig = {}
    for name, section in services.items():
        if not isinstance(name, str) or not isinstance(section, Mapping):
            raise ConfigError("Each service section must be a named TOML table")
        sections[name] = dict(section)
    return sections
