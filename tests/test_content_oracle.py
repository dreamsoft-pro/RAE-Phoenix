import json
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

# Define the root of the project and load the oracle data
PROJECT_ROOT = Path(__file__).parent.parent
ORACLE_DATA_PATH = PROJECT_ROOT / "tests" / "oracles" / "content_oracles.json"

with open(ORACLE_DATA_PATH, "r", encoding="utf-8") as f:
    oracle_data = json.load(f)

# Prepare the data for parametrization
# This converts the dictionary into a list of tuples that pytest can use
# Each tuple contains the URL and the full data object for that URL
test_cases = [(url, data) for url, data in oracle_data.items()]


def login_user(page: Page, credentials: dict):
    """Helper function to perform login."""
    page.goto("http://localtest.me/en/login")
    # Use the specific ID for the login form's email input to avoid ambiguity
    page.locator("#user-email").fill(credentials["user"])
    page.locator("input[name='password']").fill(credentials["pass"])
    page.locator("button.btn-login").click()
    # After clicking, we don't wait here. The next page's assertions will handle the wait.


@pytest.mark.skip(reason="Requires local test server")
@pytest.mark.parametrize("url,data", test_cases)
def test_page_content_oracle(page: Page, url: str, data: dict):
    """
    A data-driven test that navigates to a URL and performs a series of assertions
    based on the definitions in content_oracles.json. It also handles login if required.
    """
    base_url = "http://localtest.me"
    full_url = f"{base_url}{url}"

    # Perform login if required by the oracle data
    if "login" in data:
        login_user(page, data["login"])

    page.goto(full_url)

    assertions = data.get("assertions", [])
    for assertion in assertions:
        selector = assertion["selector"]
        assertion_type = assertion["type"]
        locator = page.locator(selector)

        if assertion_type == "visible":
            expect(locator).to_be_visible(timeout=10000)
        elif assertion_type == "count":
            expected_count = assertion["expected"]
            expect(locator).to_have_count(expected_count)
        elif assertion_type == "contains_text":
            expected_text = assertion["expected"]
            # Use .first because this assertion is for a single element's text
            expect(locator.first).to_contain_text(expected_text)
        else:
            pytest.fail(f"Unknown assertion type '{assertion_type}' in oracle data.")
