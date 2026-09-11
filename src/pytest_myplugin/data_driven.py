"""Load JSON-defined API test cases."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class ApiExpectation:
    """Expected response properties for an API case."""

    code: int


@dataclass(frozen=True, slots=True)
class ApiCase:
    """A single JSON-defined API request case."""

    case_id: str
    request_name: str
    parameters: dict[str, Any]
    expectation: ApiExpectation
    source: Path


def load_api_cases(case_directory: str | Path) -> tuple[ApiCase, ...]:
    """Load and validate all JSON API cases in a directory."""
    directory = Path(case_directory)
    case_paths = sorted(directory.rglob("*.json"))
    if not case_paths:
        raise ValueError(f"No API cases found in {directory}")

    cases = tuple(_load_case(case_path) for case_path in case_paths)
    case_ids = [case.case_id for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("API case IDs must be unique")
    return cases


def _load_case(case_path: Path) -> ApiCase:
    try:
        raw_case = json.loads(case_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in {case_path}: {error}") from error

    case = _mapping(raw_case, f"case {case_path.name}")
    _reject_unknown_keys(
        case,
        {"request_name", "parameters", "expectation"},
        f"case {case_path.name}",
    )
    request_name = _required(case, "request_name", case_path)
    parameters = _mapping(
        case.get("parameters", {}),
        f"parameters in {case_path.name}",
    )
    expectation = _mapping(
        _required(case, "expectation", case_path),
        f"expectation in {case_path.name}",
    )
    _reject_unknown_keys(
        expectation,
        {"code"},
        f"expectation in {case_path.name}",
    )

    code = expectation.get("code")
    if type(code) is not int:
        raise ValueError(f"expectation.code must be an integer in {case_path}")

    if not isinstance(request_name, str) or not request_name.strip():
        raise ValueError(f"request_name must be a non-empty string in {case_path}")

    return ApiCase(
        case_id=case_path.stem,
        request_name=request_name.strip(),
        parameters=dict(parameters),
        expectation=ApiExpectation(code=code),
        source=case_path,
    )


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _required(case: Mapping[str, Any], name: str, source: Path) -> Any:
    if name not in case:
        raise ValueError(f"{source} must define {name!r}")
    return case[name]


def _reject_unknown_keys(
    value: Mapping[str, Any],
    allowed_keys: set[str],
    label: str,
) -> None:
    unknown_keys = set(value) - allowed_keys
    if unknown_keys:
        names = ", ".join(sorted(unknown_keys))
        raise ValueError(f"Unknown field(s) in {label}: {names}")
