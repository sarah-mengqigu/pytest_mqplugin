"""Live integration test for the GitHub repository search interface."""

from __future__ import annotations

import allure
import pytest

from pytest_myplugin.services.github import GithubClient


@pytest.mark.integration
@allure.epic("GitHub")
@allure.feature("Repository Search API")
@allure.story("Search public repositories")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Search repositories through GitHub API")
def test_search_repositories(github_client: GithubClient) -> None:
    """Search public repositories through the configured GitHub client."""
    query = "pytest language:Python stars:>100"

    with allure.step(f"Search repositories with query: {query}"):
        results = github_client.search_repositories(
            query,
            sort="stars",
            order="desc",
        )

    with allure.step("Verify search results"):
        assert results.totalCount > 0

        first_result = results[0]
        assert first_result.full_name
        assert first_result.html_url.startswith("https://github.com/")
        allure.attach(
            first_result.full_name,
            name="First repository",
            attachment_type=allure.attachment_type.TEXT,
        )
