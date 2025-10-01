import pytest
from pathlib import Path
from bs4 import BeautifulSoup

# Define the root of the project and the snapshot directory
PROJECT_ROOT = Path(__file__).parent.parent
SNAPSHOT_DIR = PROJECT_ROOT / "tests" / "snapshots"

def normalize_html(html_content: str) -> str:
    """Normalize HTML content to ensure consistent comparisons."""
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.prettify()

from playwright.sync_api import TimeoutError

def test_homepage_snapshot(page):
    """
    This is a DOM snapshot test. It navigates to the homepage of the running
    application, captures the HTML of the main view, and compares it against
    a stored snapshot.
    
    If the snapshot doesn't exist, it creates it and fails the test, prompting
    the user to review and commit the new snapshot.
    """
    # 1. Define paths
    snapshot_path = SNAPSHOT_DIR / "homepage_main_view.snap.html"
    debug_screenshot_path = PROJECT_ROOT / "debug_screenshot.png"
    debug_html_path = PROJECT_ROOT / "debug_page.html"

    # 2. Navigate to the page and get the content
    page.goto("http://localtest.me/en")
    
    # The main content is rendered inside the <div ui-view></div> element.
    view_container_selector = "div[ui-view]"
    
    try:
        # Wait for a known element that indicates the homepage is loaded.
        page.wait_for_selector(f"{view_container_selector} #content-main", timeout=10000) # Reduced timeout for faster failure
    except TimeoutError:
        # If the selector is not found, save debug info.
        page.screenshot(path=str(debug_screenshot_path))
        debug_html_path.write_text(page.content(), encoding="utf-8")
        pytest.fail(
            f"Failed to find the expected selector ('{view_container_selector} .jumbotron'). "
            f"A screenshot has been saved to {debug_screenshot_path} and page HTML to {debug_html_path} for debugging."
        )
    
    # Get the inner HTML of the main view container
    main_view_element = page.query_selector(view_container_selector)
    assert main_view_element, "Main view element (ui-view) could not be found on the page."
    
    html_content = main_view_element.inner_html()
    normalized_content = normalize_html(html_content)
    
    # 3. Compare with snapshot or create it
    if snapshot_path.exists():
        # Snapshot exists, compare with it
        existing_snapshot = snapshot_path.read_text(encoding="utf-8")
        assert normalized_content == existing_snapshot, \
            f"DOM snapshot mismatch! Check for unintended changes. If the change is intentional, delete the snapshot at {snapshot_path} and re-run the test to generate a new one."
    else:
        # Snapshot does not exist, create it
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(normalized_content, encoding="utf-8")
        pytest.fail(
            f"New snapshot created at {snapshot_path}. Please review it and commit it to the repository."
        )
