"""Data-driven GitHub API cases loaded from JSON files."""

from __future__ import annotations

import json
from pathlib import Path

import allure
import pytest

from pytest_myplugin.data_driven import ApiCase, load_api_cases
from pytest_myplugin.services.github import GithubClient

API_CASES = load_api_cases(Path(__file__).parent / "cases")


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.parametrize(
    "api_case",
    API_CASES,
    ids=lambda case: case.case_id,
)
@allure.epic("GitHub")
@allure.feature("GitHub API")
@allure.story("JSON-defined API cases")
@allure.severity(allure.severity_level.CRITICAL)
def test_github_api_case(
    github_client: GithubClient,
    api_case: ApiCase,
) -> None:
    """Execute a GitHub API request defined by a JSON case."""
    allure.dynamic.title(f"GitHub API: {api_case.case_id}")

    with allure.step(f"Call GitHub API: {api_case.request_name}"):
        result = github_client.invoke(
            api_case.request_name,
            api_case.parameters,
        )

    with allure.step(f"Verify response code: {api_case.expectation.code}"):
        allure.attach(
            json.dumps(
                {
                    "case_id": api_case.case_id,
                    "request_name": api_case.request_name,
                    "parameters": api_case.parameters,
                    "response_code": result.code,
                },
                indent=2,
                sort_keys=True,
            ),
            name="API call",
            attachment_type=allure.attachment_type.JSON,
        )
        assert result.code == api_case.expectation.code
