"""Authenticated GitHub UI test."""

from __future__ import annotations

import re

import allure
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.ui
@allure.epic("GitHub")
@allure.feature("GitHub UI")
@allure.story("Authenticated user")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Authenticated user can open profile settings")
def test_github_login_and_open_profile(github_logged_in_page: Page) -> None:
    """Open the authenticated profile settings page."""
    page = github_logged_in_page

    with allure.step("Open GitHub profile settings"):
        page.goto("https://github.com/settings/profile")

    with allure.step("Verify profile settings page"):
        expect(page).to_have_url(re.compile(r"/settings/profile$"))
        expect(page.get_by_role("heading", name="Public profile")).to_be_visible()
        allure.attach(
            page.screenshot(),
            name="GitHub profile settings",
            attachment_type=allure.attachment_type.PNG,
        )
