"""Authenticated GitHub UI test."""

from __future__ import annotations

import re

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.ui
def test_github_login_and_open_profile(github_logged_in_page: Page) -> None:
    """Open the authenticated profile settings page."""
    page = github_logged_in_page
    page.goto("https://github.com/settings/profile")

    expect(page).to_have_url(re.compile(r"/settings/profile$"))
    expect(page.get_by_role("heading", name="Public profile")).to_be_visible()
