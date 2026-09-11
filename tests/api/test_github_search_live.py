"""Live integration test for the GitHub repository search interface."""

from __future__ import annotations

import pytest

from pytest_myplugin.services.github import GithubClient


@pytest.mark.integration
def test_search_repositories(github_client: GithubClient) -> None:
    """Search public repositories through the configured GitHub client."""
    results = github_client.search_repositories(
        "pytest language:Python stars:>100",
        sort="stars",
        order="desc",
    )

    assert results.totalCount > 0

    first_result = results[0]
    assert first_result.full_name
    assert first_result.html_url.startswith("https://github.com/")
