"""Playwright fixtures for authenticated GitHub UI tests."""

from __future__ import annotations

import os
import re
from collections.abc import Iterator
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from playwright.sync_api import Browser, Page

GITHUB_LOGIN_URL = "https://github.com/login"
GITHUB_LOGGED_IN_URL = re.compile(r"^https://github\.com(?:/|$)")


@pytest.fixture(scope="session")
def github_logged_in_page(browser: Browser) -> Iterator[Page]:
    """Create an authenticated GitHub page for browser tests."""
    import allure
    from playwright.sync_api import expect

    username = os.environ["GITHUB_UI_USERNAME"]
    password = os.environ["GITHUB_UI_PASSWORD"]
    context = browser.new_context()
    page = context.new_page()

    try:
        with allure.step("Open GitHub login page"):
            page.goto(GITHUB_LOGIN_URL)

        with allure.step(f"Sign in as {username}"):
            page.get_by_label("Username or email address").fill(username)
            page.get_by_label("Password").fill(password)
            page.get_by_role("button", name="Sign in").click()

        with allure.step("Verify authenticated GitHub session"):
            page.wait_for_url(GITHUB_LOGGED_IN_URL)
            expect(page).to_have_url(GITHUB_LOGGED_IN_URL)
            expect(page.locator('meta[name="user-login"]')).to_have_attribute(
                "content",
                username,
            )
            allure.attach(
                page.screenshot(),
                name="Authenticated GitHub session",
                attachment_type=allure.attachment_type.PNG,
            )

        yield page
    finally:
        context.close()
