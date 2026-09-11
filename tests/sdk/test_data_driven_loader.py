"""Tests for JSON-defined API case loading."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pytest_myplugin.data_driven import load_api_cases


def write_case(case_path: Path, payload: dict[str, object]) -> None:
    """Write a test case payload to disk."""
    case_path.parent.mkdir(parents=True, exist_ok=True)
    case_path.write_text(json.dumps(payload), encoding="utf-8")


def test_loads_nested_case_directories(tmp_path: Path) -> None:
    write_case(
        tmp_path / "github" / "search_repositories.json",
        {
            "request_name": "search_repositories",
            "parameters": {"query": "pytest"},
            "expectation": {"code": 200},
        },
    )

    cases = load_api_cases(tmp_path)

    assert len(cases) == 1
    assert cases[0].case_id == "search_repositories"
    assert cases[0].request_name == "search_repositories"
    assert cases[0].parameters == {"query": "pytest"}
    assert cases[0].expectation.code == 200


def test_rejects_unknown_fields(tmp_path: Path) -> None:
    write_case(
        tmp_path / "invalid.json",
        {
            "reuquest_name": "search_repositories",
            "parameters": {},
            "expectation": {"code": 200},
        },
    )

    with pytest.raises(ValueError, match="reuquest_name"):
        load_api_cases(tmp_path)


def test_rejects_duplicate_case_ids(tmp_path: Path) -> None:
    payload = {
        "request_name": "search_repositories",
        "parameters": {"query": "pytest"},
        "expectation": {"code": 200},
    }
    write_case(tmp_path / "one" / "search_repositories.json", payload)
    write_case(tmp_path / "two" / "search_repositories.json", payload)

    with pytest.raises(ValueError, match="case IDs must be unique"):
        load_api_cases(tmp_path)


def test_rejects_empty_case_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="No API cases found"):
        load_api_cases(tmp_path)
