"""Live integration test for authenticated Hugging Face Hub access."""

from __future__ import annotations

import allure
import pytest

from pytest_myplugin.services.huggingface import HuggingFaceClient


@pytest.mark.integration
@allure.epic("Hugging Face")
@allure.feature("Hub authentication")
@allure.story("Token validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Authenticate with Hugging Face Hub")
def test_authenticated_user(huggingface_client: HuggingFaceClient) -> None:
    """Verify that the configured HF_TOKEN belongs to a valid account."""
    with allure.step("Request authenticated Hugging Face account"):
        account = huggingface_client.whoami()

    with allure.step("Verify account information"):
        assert account.get("name")
        assert account.get("type") == "user"
        allure.attach(
            str(account.get("name")),
            name="Hugging Face account",
            attachment_type=allure.attachment_type.TEXT,
        )
