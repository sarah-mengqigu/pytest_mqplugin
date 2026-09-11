"""Environment-variable expansion for service configuration values."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from typing import Any

from .errors import ConfigError

_ENVIRONMENT_PATTERN = re.compile(
    r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}",
)


def resolve_environment(value: Any) -> Any:
    """Recursively expand ``${NAME}`` and ``${NAME:-default}`` values."""
    if isinstance(value, Mapping):
        return {str(key): resolve_environment(item) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve_environment(item) for item in value]
    if isinstance(value, str):
        return _ENVIRONMENT_PATTERN.sub(_replace_environment_value, value)
    return value


def _replace_environment_value(match: re.Match[str]) -> str:
    name, default = match.groups()
    if name in os.environ:
        return os.environ[name]
    if default is not None:
        return default
    raise ConfigError(f"Required environment variable {name!r} is not set")
